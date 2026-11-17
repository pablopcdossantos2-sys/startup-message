"""Janela da mensagem: texto, imagens, checklist e transcrições exigidas por tempo."""
from __future__ import annotations

import dataclasses
import logging
import math
import time

import customtkinter as ctk
from PIL import Image

from . import media, retype, theme, uiutil, winapi
from .config import Config
from .i18n import Translator
from .sizing import estimate_size

log = logging.getLogger(__name__)

MIN_SIZE = (560, 460)
TICK_MS = 40
PREVIEW_MAX_SECONDS = 5
STARTUP_DELAY_SECONDS = 2.0  # deixa o desktop terminar de carregar após o login
PAD = 30

TEXT_STYLES = {  # (tamanho, peso, cor)
    "heading": (22, "bold", theme.TEXT),
    "body": (16, "normal", theme.TEXT),
    "note": (13, "normal", theme.MUTED),
}


def _fmt(seconds: int) -> str:
    m, s = divmod(max(seconds, 0), 60)
    return f"{m:02d}:{s:02d}"


class MessageView(ctk.CTkFrame):
    """Conteúdo + regras de bloqueio. `win` é a janela de topo (CTk ou CTkToplevel)."""

    def __init__(self, win, cfg: Config, tr: Translator, *, seconds: int, preview: bool = False):
        super().__init__(win, fg_color=theme.BG, corner_radius=0)
        self.win, self.cfg, self.tr, self.preview = win, cfg, tr, preview
        self.total = max(1, int(seconds))
        self.locked = True
        self.time_done = False
        self._emergency_released = False
        self.vars: list[ctk.BooleanVar] = []  # itens de checklists obrigatórias
        self._typing: list[tuple[object, str, ctk.CTkLabel]] = []  # leitor, texto-alvo, estado
        self._wrap: list[tuple[ctk.CTkLabel, int]] = []
        self._imgs: list[tuple[Image.Image, ctk.CTkImage]] = []
        self._shown: int | None = None
        self._relayout_job = None
        self.accent = theme.accent(cfg.accent)
        self.accent_hover = theme.hover_of(self.accent)
        self._off_bg = theme.mix(self.accent, theme.SURFACE, 0.72)  # Ok "opaco"
        self.pack(fill="both", expand=True)
        self._build()
        if self.preview:
            # Prévia nunca pode prender o autor: X e botão de saída ficam livres.
            self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)
            self.win.bind("<Configure>", self._schedule_relayout, add="+")
        else:
            self._install_lock()
        self._refresh()
        self._end = time.monotonic() + self.total
        self._tick()
        # Segurança independente do contador: não prender a janela se o loop falhar.
        self.after(int((self.total + 5) * 1000), self._watchdog)
        self.after(150, self._relayout)
        self.after(500, self._relayout)

    # ------------------------------------------------------------ escala
    def _scale(self) -> float:
        try:
            return float(self._get_widget_scaling())
        except Exception:
            return 1.0

    # ------------------------------------------------------------ UI
    def _build(self) -> None:
        tr = self.tr
        card = ctk.CTkFrame(
            self, fg_color=theme.SURFACE, corner_radius=22,
            border_width=1, border_color=theme.BORDER,
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)  # só o conteúdo estica

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=PAD, pady=(26, 8))
        ctk.CTkFrame(head, width=44, height=6, corner_radius=3, fg_color=self.accent).pack(
            anchor="w", pady=(0, 12)
        )
        if self.cfg.title:
            lbl = ctk.CTkLabel(
                head, text=self.cfg.title, font=theme.font(self.cfg.font_size + 8, "bold", self.cfg.font_family), text_color=theme.TEXT,
                anchor="w", justify="left", wraplength=480,
            )
            lbl.pack(fill="x")
            self._wrap.append((lbl, 0))

        self.scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=theme.BORDER, scrollbar_button_hover_color=theme.MUTED,
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=(PAD - 6, PAD - 18), pady=2)
        for block in self.cfg.blocks:
            {"text": self._add_text, "image": self._add_image,
             "checklist": self._add_checklist, "retype_rules": self._add_retype_rules,
             "retype_text": self._add_retype_text}[block["type"]](block)

        ctk.CTkFrame(card, height=1, fg_color=theme.BORDER).grid(
            row=2, column=0, sticky="ew", padx=PAD
        )

        foot = ctk.CTkFrame(card, fg_color="transparent")
        foot.grid(row=3, column=0, sticky="ew", padx=PAD, pady=(14, 0))
        foot.grid_columnconfigure(0, weight=1)
        self.status = ctk.CTkLabel(
            foot, text="", font=theme.font(13), text_color=theme.MUTED,
            anchor="w", justify="left", wraplength=360,
        )
        self.status.grid(row=0, column=0, sticky="w")
        self.clock = ctk.CTkLabel(
            foot, text=_fmt(self.total), font=theme.font(34, "bold"), text_color=self.accent
        )
        self.clock.grid(row=0, column=1, sticky="e")
        self.bar = ctk.CTkProgressBar(
            foot, height=8, corner_radius=4, fg_color=theme.BORDER, progress_color=self.accent
        )
        self.bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.bar.set(1)
        self.items_label = None
        if self.vars:
            self.items_label = ctk.CTkLabel(
                foot, text="", font=theme.font(13), text_color=theme.MUTED, anchor="w"
            )
            self.items_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.typing_label = None
        if self._typing:
            self.typing_label = ctk.CTkLabel(
                foot, text="", font=theme.font(13), text_color=theme.MUTED, anchor="w"
            )
            self.typing_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self.ok = ctk.CTkButton(
            card, text=tr.t("msg.ok"), width=180, height=46, corner_radius=14,
            font=theme.font(15, "bold"), command=self._close, state="disabled",
            fg_color=self._off_bg, text_color_disabled=theme.MUTED,
        )
        self.ok.grid(row=4, column=0, pady=(18, 10 if self.preview else 26))
        if self.preview:
            ctk.CTkLabel(
                card, text=tr.t("msg.preview_note", s=min(self.total, PREVIEW_MAX_SECONDS)),
                font=theme.font(12), text_color=theme.MUTED,
            ).grid(row=5, column=0, pady=(0, 6))
            ctk.CTkButton(
                card, text=tr.t("msg.close_preview"), command=self.win.destroy,
                height=36, width=180, corner_radius=10, fg_color="transparent",
                border_width=1, border_color=theme.BORDER, text_color=theme.TEXT,
                hover_color=theme.SURFACE_ALT,
            ).grid(row=6, column=0, pady=(0, 16))

    # ------------------------------------------------------------ blocos
    def _add_text(self, b: dict) -> None:
        _size, weight, color = TEXT_STYLES[b["style"]]
        size = self.cfg.font_size + (8 if b["style"] == "heading" else -3 if b["style"] == "note" else 0)
        lbl = ctk.CTkLabel(
            self.scroll, text=b["text"], font=theme.font(size, weight, self.cfg.font_family), text_color=color,
            anchor="w", justify="left", wraplength=480,
        )
        lbl.pack(fill="x", padx=(2, 8), pady=(0, 14))
        self._wrap.append((lbl, 10))

    def _add_image(self, b: dict) -> None:
        holder = ctk.CTkFrame(self.scroll, fg_color="transparent")
        holder.pack(fill="x", padx=(2, 8), pady=(0, 14))
        path = media.resolve(b["file"])
        pil = None
        if path:
            try:
                pil = Image.open(path)
                pil.load()
            except Exception:
                log.exception("Falha ao abrir imagem %s", b["file"])
                pil = None
        if pil is None:
            ctk.CTkLabel(holder, text=self.tr.t("image.missing"), font=theme.font(13),
                         text_color=theme.MUTED).pack()
            return
        img = ctk.CTkImage(light_image=pil, dark_image=pil, size=pil.size)
        ctk.CTkLabel(holder, image=img, text="").pack()
        self._imgs.append((pil, img))
        if b.get("caption"):
            cap = ctk.CTkLabel(holder, text=b["caption"], font=theme.font(max(9, self.cfg.font_size - 3), family=self.cfg.font_family),
                               text_color=theme.MUTED, justify="center", wraplength=480)
            cap.pack(pady=(6, 0))
            self._wrap.append((cap, 10))

    def _add_checklist(self, b: dict) -> None:
        box = ctk.CTkFrame(
            self.scroll, fg_color=theme.SURFACE_ALT, corner_radius=14,
            border_width=1, border_color=theme.BORDER,
        )
        box.pack(fill="x", padx=(2, 8), pady=(0, 14))
        if b["title"]:
            t = ctk.CTkLabel(box, text=b["title"], font=theme.font(self.cfg.font_size, "bold", self.cfg.font_family),
                             text_color=theme.TEXT, anchor="w", justify="left", wraplength=420)
            t.pack(fill="x", padx=16, pady=(14, 4))
            self._wrap.append((t, 10 + 32))
        else:
            ctk.CTkFrame(box, height=6, fg_color="transparent").pack()
        for item in b["items"]:
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=5)
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                row, text="", variable=var, width=28, checkbox_width=24, checkbox_height=24,
                corner_radius=7, border_width=2, fg_color=self.accent, hover_color=self.accent_hover,
                border_color=theme.MUTED, checkmark_color=theme.ON_ACCENT, command=self._refresh,
            )
            cb.pack(side="left", anchor="n")
            lbl = ctk.CTkLabel(row, text=item, font=theme.font(self.cfg.font_size, family=self.cfg.font_family), text_color=theme.TEXT,
                               anchor="w", justify="left", wraplength=400, cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True, padx=(4, 0), pady=(1, 0))
            lbl.bind("<Button-1>", lambda _e, c=cb: c.toggle())  # clicar no texto também marca
            self._wrap.append((lbl, 10 + 32 + 32 + 28 + 4))
            if b["required"]:
                self.vars.append(var)
        ctk.CTkFrame(box, height=8, fg_color="transparent").pack()

    # ------------------------------------------------------------ transcrições obrigatórias
    def _watch_typing(self, widget) -> None:
        """Só permite resposta digitada; recalcula conclusão após cada alteração de tecla."""
        retype.prevent_paste(widget)
        widget.bind("<KeyRelease>", lambda _event: self.after_idle(self._refresh), add="+")
        widget.bind("<FocusOut>", lambda _event: self.after_idle(self._refresh), add="+")

    def _retype_card(self, title: str):
        frame = ctk.CTkFrame(
            self.scroll, fg_color=theme.SURFACE_ALT, corner_radius=14,
            border_width=1, border_color=theme.BORDER,
        )
        frame.pack(fill="x", padx=(2, 8), pady=(0, 14))
        lbl = ctk.CTkLabel(
            frame, text=title, font=theme.font(self.cfg.font_size, "bold", self.cfg.font_family),
            text_color=theme.TEXT, anchor="w", justify="left", wraplength=430,
        )
        lbl.pack(fill="x", padx=16, pady=(14, 6))
        self._wrap.append((lbl, 42))
        help_label = ctk.CTkLabel(
            frame, text=self.tr.t("msg.retype_instruction"), font=theme.font(12),
            text_color=theme.MUTED, anchor="w", justify="left", wraplength=430,
        )
        help_label.pack(fill="x", padx=16, pady=(0, 12))
        self._wrap.append((help_label, 42))
        return frame

    def _add_retype_rules(self, block: dict) -> None:
        title = block["title"] or self.tr.t("msg.retype_rules.title")
        frame = self._retype_card(title)
        for index, item in enumerate(block["items"], 1):
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(0, 14))
            prompt = ctk.CTkLabel(
                row, text=f"{index}. {item}",
                font=theme.font(self.cfg.font_size, family=self.cfg.font_family),
                text_color=theme.TEXT, anchor="w", justify="left", wraplength=400,
            )
            prompt.pack(fill="x", pady=(0, 5))
            self._wrap.append((prompt, 42))
            answer_row = ctk.CTkFrame(row, fg_color="transparent")
            answer_row.pack(fill="x")
            entry = ctk.CTkEntry(
                answer_row, height=40, corner_radius=10,
                font=theme.font(self.cfg.font_size, family=self.cfg.font_family),
                placeholder_text=self.tr.t("msg.retype_placeholder"),
                fg_color=theme.SURFACE, border_color=theme.BORDER, text_color=theme.TEXT,
            )
            entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
            indicator = ctk.CTkLabel(
                answer_row, text=self.tr.t("msg.retype_pending"), width=70,
                font=theme.font(12), text_color=theme.MUTED,
            )
            indicator.pack(side="right")
            self._typing.append((entry.get, item, indicator))
            self._watch_typing(entry)

    def _add_retype_text(self, block: dict) -> None:
        title = block["title"] or self.tr.t("msg.retype_text.title")
        frame = self._retype_card(title)
        reference = ctk.CTkLabel(
            frame, text=block["text"], font=theme.font(self.cfg.font_size, family=self.cfg.font_family),
            text_color=theme.TEXT, anchor="w", justify="left", wraplength=400,
        )
        reference.pack(fill="x", padx=16, pady=(0, 12))
        self._wrap.append((reference, 42))
        editor = ctk.CTkTextbox(
            frame, height=190, corner_radius=10, font=theme.font(self.cfg.font_size, family=self.cfg.font_family),
            border_width=1, wrap="word",
            fg_color=theme.SURFACE, border_color=theme.BORDER, text_color=theme.TEXT,
        )
        editor.pack(fill="x", padx=16, pady=(0, 6))
        indicator = ctk.CTkLabel(
            frame, text=self.tr.t("msg.retype_pending"), font=theme.font(12),
            text_color=theme.MUTED, anchor="w",
        )
        indicator.pack(anchor="w", padx=16, pady=(0, 12))
        self._typing.append((lambda field=editor: field.get("1.0", "end-1c"), block["text"], indicator))
        self._watch_typing(editor)

    # ------------------------------------------------------------ layout responsivo
    def _schedule_relayout(self, event=None) -> None:
        if event is not None and event.widget is not self.win:
            return
        if self._relayout_job is not None:
            try:
                self.after_cancel(self._relayout_job)
            except Exception:
                pass
        self._relayout_job = self.after(80, self._relayout)

    def _relayout(self) -> None:
        self._relayout_job = None
        try:
            if not self.winfo_exists():
                return
            s = self._scale()
            total_w = self.winfo_width() / s
            scroll_w = self.scroll.winfo_width() / s
            scroll_h = self.scroll.winfo_height() / s
            base = max(160.0, scroll_w - 34)  # descontando barra de rolagem e margens
            for lbl, offset in self._wrap:
                lbl.configure(wraplength=max(120, int(base - offset)))
            self.status.configure(wraplength=max(160, int(total_w - 2 * PAD - 36 - 150)))
            max_h = max(160.0, scroll_h * 0.7)
            for pil, img in self._imgs:  # escala proporcional; nunca amplia além do original
                w, h = pil.size
                k = min(1.0, (base - 10) / w, max_h / h)
                size = (max(1, int(w * k)), max(1, int(h * k)))
                if tuple(img.cget("size")) != size:
                    img.configure(size=size)
        except Exception:
            log.debug("relayout falhou", exc_info=True)

    # ------------------------------------------------------------ bloqueio
    def _install_lock(self) -> None:
        w = self.win
        w.protocol("WM_DELETE_WINDOW", self._on_close_request)
        w.resizable(True, True)  # flexível; só o "minimizar" é bloqueado
        w.attributes("-topmost", True)
        w.bind("<Unmap>", self._on_unmap, add="+")
        w.bind("<Configure>", self._schedule_relayout, add="+")
        # Enter é necessário para editar textos de transcrição com várias linhas.
        if not self._typing:
            w.bind("<Return>", lambda _e: self._close(), add="+")
        w.after(350, self._apply_native_state)  # depois do ajuste de título do CustomTkinter
        w.after(700, self._apply_native_state)
        w.lift()
        w.focus_force()

    def _apply_native_state(self) -> None:
        if not winapi.IS_WINDOWS:
            return
        try:
            if not self.winfo_exists():
                return
            hwnd = winapi.toplevel_hwnd(self.win)
            winapi.set_caption_boxes(hwnd, minimize=not self.locked, maximize=True)
            winapi.set_close_enabled(hwnd, enabled=not self.locked)  # X esmaecido
            if self.locked:
                winapi.bring_to_front(hwnd)
        except Exception:
            log.exception("Falha ao aplicar estado nativo da janela")

    def _on_close_request(self) -> None:
        self._close()

    def _on_unmap(self, event) -> None:
        if self.locked and event.widget is self.win:
            self.win.after(30, self._restore)

    def _restore(self) -> None:
        try:
            if self.locked and self.win.state() == "iconic":
                self.win.deiconify()
                self.win.lift()
        except Exception:
            pass

    def _set_locked(self, locked: bool) -> None:
        # Liberação de emergência é irreversível durante esta janela.
        if self._emergency_released:
            return
        if locked == self.locked:
            return
        self.locked = locked
        if locked:
            self.ok.configure(state="disabled", fg_color=self._off_bg)
        else:
            self.ok.configure(state="normal", fg_color=self.accent,
                              hover_color=self.accent_hover, text_color=theme.ON_ACCENT)
            self.ok.focus_set()
        if not self.preview:
            self._apply_native_state()

    # ------------------------------------------------------------ estado (tempo + itens)
    def _watchdog(self) -> None:
        try:
            if self.winfo_exists() and not self.time_done:
                log.error("Watchdog: contador não concluiu no prazo; liberando a janela")
                self._release_on_failure()
        except Exception:
            self._release_on_failure()

    def _release_on_failure(self) -> None:
        """Falha aberta permanente: nunca exigir novamente temporizador/checklist."""
        if self._emergency_released:
            return
        log.error("Erro no bloqueio; encerrando restrições por segurança", exc_info=True)
        self._emergency_released = True
        self.time_done = True
        self.locked = False
        closing_failed = False

        # Uma falha isolada de widget não deve impedir de restaurar o X nativo.
        try:
            self.ok.configure(state="normal", fg_color=self.accent,
                              hover_color=self.accent_hover, text_color=theme.ON_ACCENT)
        except Exception:
            log.exception("Não foi possível habilitar o botão OK")
            closing_failed = True
        try:
            self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)
        except Exception:
            log.exception("Não foi possível restaurar o botão de fechamento")
            closing_failed = True
        try:
            self.win.attributes("-topmost", False)
        except Exception:
            log.warning("Não foi possível remover a prioridade da janela", exc_info=True)
        if winapi.IS_WINDOWS:
            try:
                hwnd = winapi.toplevel_hwnd(self.win)
                winapi.set_close_enabled(hwnd, enabled=True)
                winapi.set_caption_boxes(hwnd, minimize=True, maximize=True)
            except Exception:
                log.exception("Não foi possível restaurar os botões nativos")
                closing_failed = True
        if closing_failed:
            # Melhor encerrar a janela do que manter a pessoa presa em um boot.
            try:
                self.win.destroy()
            except Exception:
                log.exception("Falha ao fechar janela após erro crítico")


    def _refresh(self) -> None:
        if self._emergency_released:
            return
        try:
            total = len(self.vars)
            done = sum(1 for v in self.vars if v.get())
            items_ok = done == total
            typing_total = len(self._typing)
            typing_done = 0
            for read, expected, indicator in self._typing:
                correct = retype.matches(expected, read())
                typing_done += int(correct)
                indicator.configure(
                    text=self.tr.t("msg.retype_complete" if correct else "msg.retype_pending"),
                    text_color=theme.SUCCESS if correct else theme.MUTED,
                )
            typing_ok = typing_done == typing_total
            if self.typing_label is not None:
                self.typing_label.configure(
                    text=self.tr.t("msg.typing_progress", done=typing_done, total=typing_total),
                    text_color=theme.SUCCESS if typing_ok else theme.MUTED,
                )
            if self.items_label is not None:
                self.items_label.configure(
                    text=self.tr.t("msg.items_progress", done=done, total=total),
                    text_color=theme.SUCCESS if items_ok else theme.MUTED,
                )
            if not self.time_done:
                text, color = self.tr.t("msg.wait"), theme.MUTED
            elif not items_ok and not typing_ok:
                text, color = self.tr.t("msg.need_requirements"), self.accent
            elif not items_ok:
                text, color = self.tr.t("msg.need_items"), self.accent
            elif not typing_ok:
                text, color = self.tr.t("msg.need_typing"), self.accent
            else:
                text, color = self.tr.t("msg.ready"), theme.SUCCESS
            self.status.configure(text=text, text_color=color)
            self._set_locked(not (self.time_done and items_ok and typing_ok))
        except Exception:
            self._release_on_failure()

    def _tick(self) -> None:
        if self._emergency_released:
            return
        try:
            if not self.winfo_exists():
                return
            remaining = self._end - time.monotonic()
            if remaining <= 0:
                self.time_done = True
                self.bar.set(0)
                self.clock.configure(text=_fmt(0))
                self._refresh()
                return
            secs = math.ceil(remaining)
            if secs != self._shown:
                self._shown = secs
                self.clock.configure(text=_fmt(secs))
            self.bar.set(remaining / self.total)
            self.after(TICK_MS, self._tick)
        except Exception:
            self._release_on_failure()

    def _close(self) -> None:
        if not self.locked:
            self.win.destroy()


def run_startup_message(cfg: Config, tr: Translator, *, delay_seconds: float = STARTUP_DELAY_SECONDS, smoke_test: bool = False) -> None:
    if delay_seconds:
        time.sleep(delay_seconds)
    if smoke_test:
        # Testa os widgets de transcrição mesmo com a configuração padrão vazia de exercícios.
        fixture = [
            {"type": "retype_rules", "title": "Regras", "items": ["Ler com atenção", "Seguir o plano"]},
            {"type": "retype_text", "title": "Compromisso", "text": "Exemplo de texto.\\nSegunda linha."},
        ]
        cfg = dataclasses.replace(cfg, blocks=cfg.blocks + fixture).sanitized()
    theme.apply_mode(cfg.theme)
    root = ctk.CTk(fg_color=theme.BG)
    root.title(tr.t("app.name"))
    w, h = estimate_size(cfg.blocks, cfg.font_size)
    uiutil.fit_and_center(root, w, h, min_size=MIN_SIZE, fill_height_for_large=True)
    uiutil.apply_icon(root)
    MessageView(root, cfg, tr, seconds=cfg.seconds)
    if smoke_test:
        # Executa processamento do Tk e encerra sem interação humana no CI.
        root.after(750, root.destroy)
    # O ícone é acessório: importação/execução dele nunca pode impedir a mensagem.
    tray_module = None
    tray_icon = None
    try:
        from . import tray as tray_module
        tray_icon = tray_module.start()
    except Exception:
        log.exception("Falha opcional ao iniciar ícone da bandeja")
    try:
        root.mainloop()
    finally:
        if tray_module is not None:
            try:
                tray_module.stop(tray_icon)
            except Exception:
                log.exception("Falha ao encerrar ícone da bandeja")


def open_preview(master, cfg: Config, tr: Translator):
    top = ctk.CTkToplevel(master, fg_color=theme.BG)
    top.title(f"{tr.t('app.name')} — {tr.t('msg.preview_tag')}")
    w, h = estimate_size(cfg.blocks, cfg.font_size)
    uiutil.fit_and_center(top, w, h, min_size=MIN_SIZE, fill_height_for_large=True)
    uiutil.apply_icon(top)
    top.transient(master)
    MessageView(top, cfg, tr, seconds=min(cfg.seconds, PREVIEW_MAX_SECONDS), preview=True)
    top.after(100, top.focus_force)
    return top
