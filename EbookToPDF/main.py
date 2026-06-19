import os
import tempfile
import subprocess
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ebooklib import epub
import ebooklib
from bs4 import BeautifulSoup

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def convert_mobi_to_epub_with_calibre(mobi_path: str, epub_out_path: str):
    """
    使用 Calibre 的 ebook-convert 将 MOBI 转为 EPUB。
    """
    cmd = ["ebook-convert", mobi_path, epub_out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        detail = stderr if stderr else stdout
        raise RuntimeError(f"ebook-convert 执行失败:\n{detail}")


def extract_text_from_mobi(mobi_path: str) -> str:
    """
    先将 MOBI 转为临时 EPUB，再提取正文文本。
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_epub = os.path.join(tmpdir, "temp.epub")
        convert_mobi_to_epub_with_calibre(mobi_path, temp_epub)
        book = epub.read_epub(temp_epub, options={"ignore_ncx": True})

        chunks = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text = soup.get_text(separator="\n")
                if text:
                    chunks.append(text.strip())

    full_text = "\n\n".join([c for c in chunks if c])
    # 简单清理多余空行
    lines = [line.rstrip() for line in full_text.splitlines()]
    compact = []
    blank = False
    for line in lines:
        if line.strip() == "":
            if not blank:
                compact.append("")
            blank = True
        else:
            compact.append(line)
            blank = False

    return "\n".join(compact).strip()


def wrap_text(c: canvas.Canvas, text: str, font_name: str, font_size: int, max_width: float):
    """
    按给定宽度进行基础换行。
    """
    paragraphs = text.split("\n")
    wrapped_lines = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            wrapped_lines.append("")
            continue

        words = para.split()
        if not words:
            wrapped_lines.append("")
            continue

        current = words[0]
        for w in words[1:]:
            test = current + " " + w
            if c.stringWidth(test, font_name, font_size) <= max_width:
                current = test
            else:
                wrapped_lines.append(current)
                current = w
        wrapped_lines.append(current)

    return wrapped_lines


def build_pdf(
        out_path: str,
        content_text: str,
        title: str,
        author: str,
        font_name: str,
        font_size: int,
        margins: dict,
):
    """
    生成 PDF：
    - 如果 title 非空，先生成封面（白底黑字）
    - 正文按边距和字体排版
    """
    page_width, page_height = A4
    c = canvas.Canvas(out_path, pagesize=A4)

    left = margins["left"]
    right = margins["right"]
    top = margins["top"]
    bottom = margins["bottom"]

    content_width = page_width - left - right
    line_height = font_size * 1.5

    # 封面：仅 title 非空时生成
    if title.strip():
        c.setFillColorRGB(0, 0, 0)
        # 书名
        cover_title_size = 28
        c.setFont(font_name, cover_title_size)
        tw = c.stringWidth(title, font_name, cover_title_size)
        c.drawString((page_width - tw) / 2, page_height * 0.60, title)

        # 作者（可选）
        if author.strip():
            cover_author_size = 16
            c.setFont(font_name, cover_author_size)
            aw = c.stringWidth(author, font_name, cover_author_size)
            c.drawString((page_width - aw) / 2, page_height * 0.52, author)

        c.showPage()

    # 正文
    c.setFont(font_name, font_size)
    y = page_height - top

    lines = wrap_text(c, content_text, font_name, font_size, content_width)
    for line in lines:
        if y < bottom:
            c.showPage()
            c.setFont(font_name, font_size)
            y = page_height - top

        c.drawString(left, y, line)
        y -= line_height

    c.save()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MOBI 转 PDF")
        self.geometry("680x520")
        self.resizable(False, False)

        self.mobi_path = tk.StringVar(value="")
        self.title_text = tk.StringVar(value="")
        self.author_text = tk.StringVar(value="")

        # 默认字体名称（reportlab 内置）
        self.font_name = tk.StringVar(value="Helvetica")
        self.font_size = tk.IntVar(value=12)

        self.margin_top = tk.IntVar(value=72)     # 1 inch
        self.margin_bottom = tk.IntVar(value=72)
        self.margin_left = tk.IntVar(value=72)
        self.margin_right = tk.IntVar(value=72)

        self.custom_font_file = tk.StringVar(value="")
        self.custom_font_registered_name = None

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        # 文件选择
        ttk.Label(frm, text="MOBI 文件:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.mobi_path, width=58).grid(row=0, column=1, sticky="w", **pad)
        ttk.Button(frm, text="浏览...", command=self.pick_mobi).grid(row=0, column=2, sticky="w", **pad)

        # 书名 / 作者
        ttk.Label(frm, text="书名(可选):").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.title_text, width=30).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(frm, text="作者(可选):").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.author_text, width=30).grid(row=2, column=1, sticky="w", **pad)

        # 字体设置
        ttk.Label(frm, text="内置字体:").grid(row=3, column=0, sticky="w", **pad)
        font_combo = ttk.Combobox(
            frm,
            textvariable=self.font_name,
            values=["Helvetica", "Times-Roman", "Courier"],
            state="readonly",
            width=27,
        )
        font_combo.grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(frm, text="字体大小:").grid(row=4, column=0, sticky="w", **pad)
        ttk.Spinbox(frm, from_=8, to=36, textvariable=self.font_size, width=10).grid(row=4, column=1, sticky="w", **pad)

        ttk.Button(frm, text="选择自定义字体(.ttf)", command=self.pick_ttf_font).grid(row=5, column=1, sticky="w", **pad)
        ttk.Label(frm, textvariable=self.custom_font_file, foreground="#666").grid(row=6, column=1, sticky="w", **pad)

        # 边距
        ttk.Label(frm, text="上边距(pt):").grid(row=7, column=0, sticky="w", **pad)
        ttk.Spinbox(frm, from_=18, to=180, textvariable=self.margin_top, width=10).grid(row=7, column=1, sticky="w", **pad)

        ttk.Label(frm, text="下边距(pt):").grid(row=8, column=0, sticky="w", **pad)
        ttk.Spinbox(frm, from_=18, to=180, textvariable=self.margin_bottom, width=10).grid(row=8, column=1, sticky="w", **pad)

        ttk.Label(frm, text="左边距(pt):").grid(row=9, column=0, sticky="w", **pad)
        ttk.Spinbox(frm, from_=18, to=180, textvariable=self.margin_left, width=10).grid(row=9, column=1, sticky="w", **pad)

        ttk.Label(frm, text="右边距(pt):").grid(row=10, column=0, sticky="w", **pad)
        ttk.Spinbox(frm, from_=18, to=180, textvariable=self.margin_right, width=10).grid(row=10, column=1, sticky="w", **pad)

        # 操作按钮
        ttk.Separator(frm, orient="horizontal").grid(row=11, column=0, columnspan=3, sticky="ew", pady=14)
        ttk.Button(frm, text="开始转换并保存 PDF", command=self.convert).grid(row=12, column=1, sticky="w", **pad)

        hint = (
            "说明:\n"
            "1) 先选择 .mobi 文件\n"
            "2) 可填写书名和作者（书名不为空则自动生成封面）\n"
            "3) 可选内置字体或加载 .ttf 自定义字体\n"
            "4) 点击转换后选择 PDF 保存位置"
        )
        ttk.Label(frm, text=hint, foreground="#444", justify="left").grid(row=13, column=0, columnspan=3, sticky="w", padx=10, pady=10)

    def pick_mobi(self):
        path = filedialog.askopenfilename(
            title="选择 MOBI 文件",
            filetypes=[("MOBI files", "*.mobi"), ("All files", "*.*")],
        )
        if path:
            self.mobi_path.set(path)

    def pick_ttf_font(self):
        path = filedialog.askopenfilename(
            title="选择 TTF 字体文件",
            filetypes=[("TrueType Font", "*.ttf"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            font_id = "CustomTTF"
            pdfmetrics.registerFont(TTFont(font_id, path))
            self.custom_font_registered_name = font_id
            self.custom_font_file.set(os.path.basename(path))
            messagebox.showinfo("字体已加载", f"已加载字体: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("字体加载失败", f"无法加载字体:\n{e}")

    def validate(self):
        mobi = self.mobi_path.get().strip()
        if not mobi:
            messagebox.showwarning("提示", "请先选择 MOBI 文件。")
            return False
        if not os.path.exists(mobi):
            messagebox.showwarning("提示", "MOBI 文件不存在。")
            return False

        margins = [self.margin_top.get(), self.margin_bottom.get(), self.margin_left.get(), self.margin_right.get()]
        if any(m < 18 for m in margins):
            messagebox.showwarning("提示", "边距建议不小于 18 pt。")
            return False

        return True

    def convert(self):
        if not self.validate():
            return

        save_path = filedialog.asksaveasfilename(
            title="保存 PDF 文件",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not save_path:
            return

        try:
            mobi = self.mobi_path.get().strip()
            title = self.title_text.get().strip()
            author = self.author_text.get().strip()

            final_font = self.custom_font_registered_name if self.custom_font_registered_name else self.font_name.get()

            text = extract_text_from_mobi(mobi)
            if not text:
                messagebox.showwarning("提示", "未能从 MOBI 中提取到文本内容。")
                return

            margins = {
                "top": self.margin_top.get(),
                "bottom": self.margin_bottom.get(),
                "left": self.margin_left.get(),
                "right": self.margin_right.get(),
            }

            build_pdf(
                out_path=save_path,
                content_text=text,
                title=title,
                author=author,
                font_name=final_font,
                font_size=self.font_size.get(),
                margins=margins,
            )

            messagebox.showinfo("完成", f"转换成功!\nPDF 已保存到:\n{save_path}")
        except FileNotFoundError:
            messagebox.showerror(
                "缺少依赖",
                "未找到 ebook-convert 命令。\n\n"
                "请先安装 Calibre，并确保 ebook-convert 在系统 PATH 中。"
            )
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("转换失败", f"发生错误:\n{e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()