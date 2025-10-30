import os
import shutil

# 设置源文件夹和目标文件夹路径
source_folder = r"C:\Users\zjh\Desktop\AI东雪莲"
target_folder = r"C:\Users\zjh\Desktop\东雪莲lora训练\图片合集"

# 创建目标文件夹（如果不存在）
os.makedirs(target_folder, exist_ok=True)

# 支持的图片格式
image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'}

# 计数器
moved_count = 0

# 遍历源文件夹及其所有子文件夹
for root, dirs, files in os.walk(source_folder):
    for filename in files:
        # 获取文件扩展名（转换为小写以支持大小写不同的情况）
        file_extension = os.path.splitext(filename)[1].lower()

        # 如果是图片文件
        if file_extension in image_extensions:
            # 源文件路径
            source_path = os.path.join(root, filename)
            # 目标文件路径（为了避免重名，可以添加前缀）
            target_filename = f"{os.path.basename(root)}_{filename}"  # 添加文件夹名前缀
            target_path = os.path.join(target_folder, target_filename)

            try:
                # 移动文件
                shutil.move(source_path, target_path)
                print(f"已移动: {source_path} -> {target_path}")
                moved_count += 1
            except Exception as e:
                print(f"移动失败 {source_path}: {e}")

print(f"移动完成！共移动了 {moved_count} 个图片文件")