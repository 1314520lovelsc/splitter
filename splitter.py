import os
import sys
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
 
def resource_path(relative_path):
    """适配打包后的资源路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
 
class FileSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("分割器极速版 v1.0")  # 自定义窗口标题
        self.root.geometry("600x400")
 
        # 关键：设置窗口左上角小图标
        self.root.iconbitmap(resource_path("mylogo.ico"))
 
        self.input_files = []
        self.records_per_file = tk.StringVar(value="5000")
        self.max_size_mb = tk.StringVar(value="10")
        self.stop_flag = False  # 中断控制标志
 
        # UI布局
        tk.Label(root, text="请选择文件（支持批量 JSON/TXT/CSV）:").pack(pady=5)
        tk.Button(root, text="选择文件", command=self.select_files).pack(pady=5)
 
        tk.Label(root, text="每份最多记录数（条目/行）（可留空）:").pack(pady=5)
        tk.Entry(root, textvariable=self.records_per_file).pack(pady=5)
 
        tk.Label(root, text="每份最大大小（MB）（可留空）:").pack(pady=5)
        tk.Entry(root, textvariable=self.max_size_mb).pack(pady=5)
 
        tk.Button(root, text="开始分割", command=self.start_split).pack(pady=10)
        tk.Button(root, text="退出程序", command=self.exit_program).pack(pady=5)
 
        tk.Label(root, text="当前进度:").pack(pady=5)
        self.progress = Progressbar(root, length=500, mode="determinate")
        self.progress.pack(pady=5)
 
    def select_files(self):
        self.input_files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[("支持文件", "*.json *.txt *.csv")]
        )
 
    def start_split(self):
        if not self.input_files:
            messagebox.showerror("错误", "请先选择至少一个文件！")
            return
 
        try:
            records_input = self.records_per_file.get().strip()
            size_input = self.max_size_mb.get().strip()
 
            records = int(records_input) if records_input else None
            size_mb = float(size_input) if size_input else None
 
            if records is None and size_mb is None:
                messagebox.showerror("错误", "请至少填写记录数或大小其中一个条件！")
                return
        except ValueError:
            messagebox.showerror("错误", "记录数应为整数，大小应为数字！")
            return
 
        self.stop_flag = False
        threading.Thread(target=self.batch_split, args=(records, size_mb)).start()
 
    def batch_split(self, records_per_file, max_size_mb):
        try:
            for file_path in self.input_files:
                if self.stop_flag:
                    print("中断处理（批量阶段）")
                    return
 
                file_base_name, file_ext = os.path.splitext(os.path.basename(file_path))
                output_folder = os.path.join(os.path.dirname(file_path), file_base_name)
                os.makedirs(output_folder, exist_ok=True)
 
                if file_ext.lower() == ".json":
                    self.split_json(file_path, file_base_name, output_folder, records_per_file, max_size_mb)
                elif file_ext.lower() in [".txt", ".csv"]:
                    self.split_text(file_path, file_base_name, output_folder, records_per_file, max_size_mb)
                else:
                    messagebox.showwarning("警告", f"暂不支持的文件类型: {file_ext}")
        except Exception as e:
            if not self.stop_flag:
                messagebox.showerror("错误", f"处理失败: {e}")
 
    def split_json(self, file_path, file_base_name, output_folder, records_per_file, max_size_mb):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
 
        total_records = len(data)
        self.progress["maximum"] = total_records
 
        chunk = []
        size_counter = 0
        count = 0
 
        for idx, item in enumerate(data):
            if self.stop_flag:
                print("中断处理（JSON）")
                return
 
            chunk.append(item)
            size_counter += len(json.dumps(item, ensure_ascii=False).encode('utf-8')) + 2
 
            if (records_per_file and len(chunk) >= records_per_file) or \
               (max_size_mb and size_counter >= max_size_mb * 1024 * 1024):
                out_file = os.path.join(output_folder, f"{file_base_name}_part_{count:03}.json")
                with open(out_file, "w", encoding="utf-8") as f_out:
                    json.dump(chunk, f_out, ensure_ascii=False, indent=2)
                chunk = []
                size_counter = 0
                count += 1
 
            if idx % 100 == 0:
                self.progress["value"] = idx
                self.root.update_idletasks()
 
        if chunk:
            out_file = os.path.join(output_folder, f"{file_base_name}_part_{count:03}.json")
            with open(out_file, "w", encoding="utf-8") as f_out:
                json.dump(chunk, f_out, ensure_ascii=False, indent=2)
 
    def split_text(self, file_path, file_base_name, output_folder, records_per_file, max_size_mb):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
 
        total_records = len(lines)
        self.progress["maximum"] = total_records
 
        chunk = []
        size_counter = 0
        count = 0
 
        for idx, line in enumerate(lines):
            if self.stop_flag:
                print("中断处理（TXT）")
                return
 
            chunk.append(line)
            size_counter += len(line.encode('utf-8'))
 
            if (records_per_file and len(chunk) >= records_per_file) or \
               (max_size_mb and size_counter >= max_size_mb * 1024 * 1024):
                out_file = os.path.join(output_folder, f"{file_base_name}_part_{count:03}.txt")
                with open(out_file, "w", encoding="utf-8") as f_out:
                    f_out.writelines(chunk)
                chunk = []
                size_counter = 0
                count += 1
 
            if idx % 100 == 0:
                self.progress["value"] = idx
                self.root.update_idletasks()
 
        if chunk:
            out_file = os.path.join(output_folder, f"{file_base_name}_part_{count:03}.txt")
            with open(out_file, "w", encoding="utf-8") as f_out:
                f_out.writelines(chunk)
 
    def exit_program(self):
        if messagebox.askokcancel("退出确认", "确定要退出程序吗？正在处理中也会立即终止！"):
            self.stop_flag = True
            self.root.destroy()
 
if __name__ == "__main__":
    root = tk.Tk()
    app = FileSplitterApp(root)
    root.mainloop()