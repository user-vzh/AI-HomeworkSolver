import tkinter as tk
from tkinter import filedialog, scrolledtext, Menu, simpledialog
import fitz  # PyMuPDF
import requests
import json
import threading

LLAMA_ENDPOINT = "http://localhost:11434/api/chat"
LLAMA_MODEL = "llama3.1:8b"

# === LLaMA query ===
def query_llama(content, system_prompt="You are a helpful tutor. Please solve the following question:"):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content}
    ]

    response = requests.post(
        LLAMA_ENDPOINT,
        json={"model": LLAMA_MODEL, "messages": messages, "stream": True},
        stream=True
    )

    result = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8'))
                result += data.get("message", {}).get("content", "")
            except:
                continue
    return result

# === PDF to text ===
def extract_text_from_pdf(path):
    doc = fitz.open(path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text.strip()

# === GUI ===
class PDFSolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Solver with LLaMA 3.1")
        self.root.geometry("1200x700")

        # Main Text Area
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_area.bind("<Button-3>", self.show_context_menu)

        # Context Menu
        self.menu = Menu(root, tearoff=0)
        self.menu.add_command(label="Solve", command=self.solve_selected)
        self.menu.add_command(label="Prompt", command=self.prompt_custom)

        # Answer Panel
        self.answer_frame = tk.Frame(root, width=300, bg="#f4f4f4", relief=tk.RAISED, bd=2)
        self.answer_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.answer_label = tk.Label(self.answer_frame, text="Answer", font=("Arial", 14, "bold"), bg="#f4f4f4")
        self.answer_label.pack(pady=10)
        self.answer_text = scrolledtext.ScrolledText(self.answer_frame, wrap=tk.WORD, height=30)
        self.answer_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open PDF", command=self.open_pdf)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=self.menu_bar)

    def open_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            text = extract_text_from_pdf(path)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, text)

    def show_context_menu(self, event):
        try:
            self.text_area.tag_add("sel", "@%d,%d" % (event.x, event.y), "insert wordend")
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def solve_selected(self):
        selected_text = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
        if selected_text.strip():
            self.answer_text.delete(1.0, tk.END)
            self.answer_text.insert(tk.END, "Thinking...")

            def solve_thread():
                answer = query_llama(selected_text)
                self.answer_text.delete(1.0, tk.END)
                self.answer_text.insert(tk.END, answer)

            threading.Thread(target=solve_thread).start()

    def prompt_custom(self):
        selected_text = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
        if selected_text.strip():
            prompt = simpledialog.askstring("Custom Prompt", "Enter your prompt:")
            if prompt:
                self.answer_text.delete(1.0, tk.END)
                self.answer_text.insert(tk.END, "Thinking...")

                def prompt_thread():
                    answer = query_llama(selected_text, system_prompt=prompt)
                    self.answer_text.delete(1.0, tk.END)
                    self.answer_text.insert(tk.END, answer)

                threading.Thread(target=prompt_thread).start()

# === Run app ===
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSolverApp(root)
    root.mainloop()
