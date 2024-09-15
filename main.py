import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import ImageTk, Image
import fitz  # PyMuPDF


class rw:
    def __init__(self, root):
        self.root = root
        self.root.title("Ankha PDF Reader version: Stable 1.5.8")
        self.root.geometry("1920x1080")

        # Initialize drawing state and tool settings
        self.pen_size = 1
        self.eraser_size = 10
        self.current_tool = 'pen'
        self.drawing = False
        self.pen_color = 'black'  # Default pen color
        self.pdf_document = None
        self.current_page = 0
        self.x_offset = 0
        self.y_offset = 0
        self.zoom_factor = 1.0  # Initial zoom factor
        self.hand_mode = False  # Track whether hand mode is active

        # Create the drawing area (canvas)
        self.canvas = tk.Canvas(self.root, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Initialize the whiteboard
        self.whiteboard()

        # Add buttons, slider, and color palette to the toolbox
        self.create_toolbox()

        # Initialize and show startup image
        self.init_startup_image()

    def show_info(self):
        # Show an info message
        messagebox.showinfo("HI", "Thanks for using Ankha Smart Board")

    def init_startup_image(self):
        # Load and display the startup image
        try:
            self.start_image_tk = ImageTk.PhotoImage(Image.open("ankha.png"))
            self.start_label = tk.Label(self.root, image=self.start_image_tk)
            self.start_label.pack(fill=tk.BOTH, expand=True)
        except FileNotFoundError:
            messagebox.showerror("Error", "Startup image 'ankha.png' not found!")
            self.root.after(2000, self.initialize_viewer)  # Skip the image display if file not found
        else:
            # Hide the image after 2 seconds and initialize the main viewer
            self.root.after(2000, self.initialize_viewer)

    def initialize_viewer(self):
        # Remove the startup image and show the main interface
        if hasattr(self, 'start_label'):
            self.start_label.pack_forget()
        self.show_info()  # Show the info message after startup

    def create_toolbox(self):
        # Create a frame to act as the toolbox on the right side
        toolbox = tk.Frame(self.root, width=100, bg='lightgray')
        toolbox.pack(side="right", fill="y")

        # Add buttons to the toolbox
        button1 = tk.Button(toolbox, text="Pen", command=self.activate_pencil)
        button1.pack(pady=10, padx=10, fill='x')

        button2 = tk.Button(toolbox, text="Eraser", command=self.activate_eraser)
        button2.pack(pady=10, padx=10, fill='x')

        button3 = tk.Button(toolbox, text="Clear", command=self.clear_canvas)
        button3.pack(pady=10, padx=10, fill='x')

        button4 = tk.Button(toolbox, text="Hand", command=self.activate_hand)
        button4.pack(pady=10, padx=10, fill='x')

        button5 = tk.Button(toolbox, text="Create Whiteboard", command=self.whiteboard)
        button5.pack(pady=10, padx=10, fill='x')

        # Create a frame for the sliders
        slider_frame = tk.Frame(toolbox, bg='lightgray')
        slider_frame.pack(pady=10, padx=10, fill='x')

        # Eraser Size Slider
        self.eraser_slider = tk.Scale(slider_frame, from_=1, to=50, orient=tk.HORIZONTAL, command=self.on_eraser_slide)
        self.eraser_slider.set(self.eraser_size)  # Set the initial value of the slider
        self.eraser_slider.pack(padx=10, fill="x")

        # Pen Size Slider
        self.pen_slider = tk.Scale(slider_frame, from_=1, to=10, orient=tk.HORIZONTAL, command=self.on_pen_slide)
        self.pen_slider.set(self.pen_size)  # Set the initial value of the slider
        self.pen_slider.pack(padx=10, fill="x")

        # Create a frame for the color palette
        color_frame = tk.Frame(toolbox, bg='lightgray')
        color_frame.pack(pady=10, padx=10, fill='x')

        # Add color buttons to the color palette
        colors = ['black', 'red', 'green', 'blue', 'yellow', 'orange', 'purple', 'brown']
        for color in colors:
            button = tk.Button(color_frame, bg=color, width=2, height=2, command=lambda c=color: self.set_pen_color(c))
            button.pack(side=tk.LEFT, padx=2, pady=2)

        # Open PDF button
        open_pdf_button = tk.Button(toolbox, text="Open a PDF", command=self.open_pdf)
        open_pdf_button.pack(pady=10, padx=10, fill='x')

        # Page navigation buttons
        nav_frame = tk.Frame(toolbox, bg='lightgray')
        nav_frame.pack(pady=10, padx=10, fill='x')

        self.prev_button = tk.Button(nav_frame, text="◀", command=self.previous_page)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.page_label = tk.Label(nav_frame, text="Page: 0")
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(nav_frame, text="▶", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=5)

        # Zoom buttons
        zoom_frame = tk.Frame(toolbox, bg='lightgray')
        zoom_frame.pack(pady=10, padx=10, fill='x')

        zoom_in_button = tk.Button(zoom_frame, text="Zoom In", command=self.zoom_in)
        zoom_in_button.pack(side=tk.LEFT, padx=5)

        zoom_out_button = tk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out)
        zoom_out_button.pack(side=tk.LEFT, padx=5)

    def set_pen_color(self, color):
        self.pen_color = color

    def activate_pencil(self):
        self.current_tool = 'pen'
        self.hand_mode = False
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<Button-1>", self.start_drawing)

    def activate_eraser(self):
        self.current_tool = 'eraser'
        self.hand_mode = False
        self.canvas.bind("<B1-Motion>", self.erase)
        self.canvas.bind("<Button-1>", self.start_eraser)

    def activate_hand(self):
        self.current_tool = 'hand'
        self.hand_mode = True
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<Button-1>", self.on_mouse_down)

    def start_drawing(self, event):
        if not self.hand_mode:
            self.drawing = True
            self.last_x, self.last_y = event.x, event.y

    def draw(self, event):
        if self.drawing and self.current_tool == 'pen':
            x, y = event.x, event.y
            self.canvas.create_line(self.last_x, self.last_y, x, y, fill=self.pen_color, width=self.pen_size)
            self.last_x, self.last_y = x, y

    def start_eraser(self, event):
        if not self.hand_mode:
            self.drawing = True
            self.last_x, self.last_y = event.x, event.y

    def erase(self, event):
        if self.drawing and self.current_tool == 'eraser':
            x, y = event.x, event.y
            self.canvas.create_oval(x - self.eraser_size, y - self.eraser_size, x + self.eraser_size, y + self.eraser_size, fill='white', outline='white')
            self.last_x, self.last_y = x, event.y

    def stop_drawing(self, event):
        self.drawing = False

    def clear_canvas(self):
        self.canvas.delete("all")

    def open_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.pdf_document = fitz.open(file_path)
            self.current_page = 0
            self.zoom_factor = 1.0
            self.show_page(self.current_page)

    def show_page(self, page_number):
        if self.pdf_document:
            page = self.pdf_document.load_page(page_number)
            pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_factor, self.zoom_factor))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.img_tk = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(self.x_offset, self.y_offset, image=self.img_tk, anchor=tk.NW)
            self.page_label.config(text=f"Page: {page_number + 1}")

    def previous_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def next_page(self):
        if self.pdf_document and self.current_page < self.pdf_document.page_count - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def whiteboard(self):
        self.canvas.delete("all")
        self.canvas.config(bg='white')
        self.x_offset = 0
        self.y_offset = 0
        self.canvas.bind("<B1-Motion>", lambda e: None)  # Disable dragging on the whiteboard

    def on_eraser_slide(self, value):
        self.eraser_size = int(value)

    def on_pen_slide(self, value):
        self.pen_size = int(value)

    def zoom_in(self):
        self.zoom_factor *= 1.2
        if self.pdf_document:
            self.show_page(self.current_page)

    def zoom_out(self):
        self.zoom_factor /= 1.2
        if self.pdf_document:
            self.show_page(self.current_page)

    def on_mouse_down(self, event):
        if self.pdf_document and self.hand_mode:
            self.start_x = event.x
            self.start_y = event.y

    def on_mouse_drag(self, event):
        if self.pdf_document and self.hand_mode:
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            self.x_offset += dx
            self.y_offset += dy
            self.canvas.delete("all")
            self.show_page(self.current_page)
            self.start_x = event.x
            self.start_y = event.y


if __name__ == "__main__":
    root = tk.Tk()
    app = rw(root)
    root.mainloop()
