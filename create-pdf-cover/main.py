import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ================= 配置区域 =================
TITLES_TO_GENERATE = [
    "历久弥新的十字架",
    "基督生平简介",
    "异象与使命（下）",
    "灵命进深"
]

OUTPUT_DIR_NAME = "cover"
# ===========================================

def get_font_config():
    """
    配置中文字体，返回可用的字体名称
    """
    # ------------------- 修改点 1：更改为楷体路径 -------------------
    # Windows 默认楷体路径 (SimKai)
    font_path_win = "C:/Windows/Fonts/simkai.ttf"
    
    # Mac 用户如果需要楷体，通常路径是:
    # font_path_mac = "/System/Library/Fonts/STKaiti.ttc" 
    
    font_name = 'Helvetica' # 默认回退字体

    if os.path.exists(font_path_win):
        try:
            # 注册字体，命名为 '楷体'
            pdfmetrics.registerFont(TTFont('楷体', font_path_win))
            font_name = '楷体'
        except Exception as e:
            print(f"字体加载失败: {e}")
    else:
        print("警告：未找到中文字体文件，中文将无法显示。请检查代码中的 font_path 设置。")
        
    return font_name

def create_cover(title_text, save_dir):
    """
    生成单个封面 PDF
    """
    filename = f"{title_text}_封面.pdf"
    full_path = os.path.join(save_dir, filename)

    # 1. 创建画布
    c = canvas.Canvas(full_path, pagesize=A4)
    width, height = A4
    
    # 2. 获取字体配置
    font_name = get_font_config()


    # 4. 写入主标题 (居中)
    c.setFont(font_name, 48)
    
    # ------------------- 修改点 2：调整垂直位置 -------------------
    # 原来是 +30，现在改为 +120，数字越大越靠上
    c.drawCentredString(width / 2.0, height / 2.0 + 120, title_text)

    # 保存
    c.save()
    print(f"✅ 已生成: {full_path}")

if __name__ == "__main__":
    current_path = os.getcwd()
    target_folder = os.path.join(current_path, OUTPUT_DIR_NAME)

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        print(f"📂 新建文件夹: {target_folder}")
    else:
        print(f"📂 使用现有文件夹: {target_folder}")

    print("--- 开始批量生成 (楷体版) ---")
    for title in TITLES_TO_GENERATE:
        create_cover(title, target_folder)
    print("--- 全部完成 ---")