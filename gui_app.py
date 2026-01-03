import tkinter as tk
from tkinter import ttk, messagebox
import backend
import threading
import queue

class BistTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BIST 100 Takipçisi")
        self.root.geometry("600x500")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header_frame = ttk.Frame(root, padding="10")
        header_frame.pack(fill=tk.X)
        
        self.fetch_btn = ttk.Button(header_frame, text="Verileri Getir / Güncelle", command=self.start_fetching)
        self.fetch_btn.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header_frame, text="Hazır")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Progress Bar
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # Table
        columns = ('ticker', 'price', 'change', 'status')
        self.tree = ttk.Treeview(root, columns=columns, show='headings')
        
        self.tree.heading('ticker', text='Sembol')
        self.tree.heading('price', text='Fiyat (TL)')
        self.tree.heading('change', text='5 Günlük Değişim (%)')
        self.tree.heading('status', text='Durum')
        
        self.tree.column('ticker', width=80)
        self.tree.column('price', width=100)
        self.tree.column('change', width=120)
        self.tree.column('status', width=150)
        
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Queue for thread communication
        self.queue = queue.Queue()
        self.root.after(100, self.process_queue)

    def start_fetching(self):
        self.fetch_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Liste alınıyor...")
        self.progress['value'] = 0
        
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        threading.Thread(target=self.fetch_data_thread, daemon=True).start()

    def fetch_data_thread(self):
        try:
            # 1. Get List
            symbols = backend.get_bist100_list()
            if not symbols:
                self.queue.put(("error", "Hisse listesi alınamadı."))
                return

            self.queue.put(("update_status", f"{len(symbols)} hisse bulundu. Veriler çekiliyor..."))
            self.queue.put(("set_max_progress", len(symbols)))
            
            # 2. Fetch Data Loop
            for i, ticker in enumerate(symbols):
                # Fetch single stock data
                result = backend.get_stock_data_single(ticker)
                # content: (ticker, price, change, status)
                self.queue.put(("add_row", result))
                self.queue.put(("progress_step", 1))
                
            self.queue.put(("done", None))
            
        except Exception as e:
            self.queue.put(("error", str(e)))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                
                if msg_type == "update_status":
                    self.status_label.config(text=data)
                elif msg_type == "set_max_progress":
                    self.progress['maximum'] = data
                elif msg_type == "progress_step":
                    self.progress.step(data)
                elif msg_type == "add_row":
                    ticker, price, change, status = data
                    # Color coding for change
                    tags = ()
                    if change > 0: tags = ('green',)
                    elif change < 0: tags = ('red',)
                    
                    self.tree.insert('', tk.END, values=(ticker, f"{price:.2f}", f"{change:.2f}", status), tags=tags)
                elif msg_type == "done":
                    self.status_label.config(text="Tamamlandı.")
                    self.fetch_btn.config(state=tk.NORMAL)
                    messagebox.showinfo("Bilgi", "Veri çekme işlemi tamamlandı.")
                elif msg_type == "error":
                    self.status_label.config(text="Hata oluştu.")
                    self.fetch_btn.config(state=tk.NORMAL)
                    messagebox.showerror("Hata", data)
                    
                self.queue.task_done()
        except queue.Empty:
            pass
            
        self.tree.tag_configure('green', foreground='green')
        self.tree.tag_configure('red', foreground='red')
        
        self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = BistTrackerApp(root)
    root.mainloop()
