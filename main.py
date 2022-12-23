import tkinter as tk
import tkinter.messagebox
from tkinter.ttk import *
from PIL import ImageTk, Image
import os

# TODO: take root directory from config.json file
root_dir = 'input'

dir_tree = {}
for dirpath, dirnames, filenames in os.walk(root_dir):
    parts = dirpath.split(os.sep)
    curr = dir_tree
    if len(dirnames):
        for p in parts:
            curr = curr.setdefault(p, {})
    else:
        for p in parts:
            curr = curr.setdefault(p, [file for file in filenames])


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        for ix, _dir in enumerate(dir_tree[root_dir].keys()):
            self.button = tk.Button(self, text=_dir, command=lambda k=_dir: self.on_button_click(k))
            self.button.pack(side='left', padx=20)
            # self.button.place(relx=0.5, rely=0.5, anchor='center')

        self.pack(side="top", fill="both", expand=True)
        # self.place(relx=0.5, rely=0.5, anchor='center')

    def on_button_click(self, button_name):
        self.master.switch_frame(SecondWindow, button_name)


class SecondWindow(tk.Frame):
    def __init__(self, master=None, button_name=None):
        super().__init__(master)
        self.master = master
        self.button_name = button_name
        self.file_paths = [os.path.join(root_dir, self.button_name, cl) for cl in dir_tree[root_dir][button_name].keys()]
        print(self.file_paths)
        self.current_image_index = 0
        # self.image_filename = tk.StringVar()

        self.label = tk.Label(self)
        self.label.pack(side='top')
        # self.label.place(relx=0.5, rely=0.5, anchor='n')

        # Create a label to display the image
        self.image_label = tk.Label(self)
        self.image_label.pack()
        # self.image_label.place(relx=0.5, rely=0.5, anchor='center')

        self.back_button_frame = tk.Frame(self)
        self.back_button_frame.pack(side='bottom')

        self.back_button = tk.Button(self.back_button_frame, text="Main Menu", command=lambda: self.on_back_click())
        self.back_button.pack(side="left", padx=20, pady=20)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side='bottom')
        # self.button_frame.place(relx=0.5, rely=1, anchor='s')

        # Create buttons to move to the next or previous image
        self.prev_button = tk.Button(self.button_frame, text="Previous", command=self.on_prev_click)
        self.prev_button.pack(side="left", padx=20, pady=20)
        # self.prev_button.place(relx=0, rely=1, anchor='sw')

        self.next_button = tk.Button(self.button_frame, text="Next", command=self.on_next_click)
        self.next_button.pack(side="left", padx=20, pady=20)
        # self.prev_button.place(relx=1, rely=1, anchor='se')

        self.radio_frame = tk.Frame(self)
        self.radio_frame.pack(side='bottom')

        self.selected_option = tk.StringVar()

        for lab in dir_tree[root_dir][button_name].keys():
            self.option_radio = tk.Radiobutton(self.radio_frame, text=lab, variable=self.selected_option, value=lab)
            self.option_radio.pack(side='left')



        # Display the first image
        self.display_images()

        # self.pack(side="top", fill="both", expand=True)
        # self.place(relx=0.5, rely=0.5, anchor='center')
        self.pack()


    def on_next_click(self):
        self.current_image_index += 1
        self.display_images()

    def on_prev_click(self):
        self.current_image_index -= 1
        self.display_images()

    def set_image_filename(self, image_path):
        self.image_filename.set(image_path)

    def display_images(self):
        # TODO: Move this to SecondWindow class - no need to run it every time func is called
        filenames = []
        try:
            for pathe in self.file_paths:
                filenames += [os.path.join(pathe, f) for f in os.listdir(pathe) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        except OSError:
            tk.messagebox.showerror("Error", "Invalid directory path")
            self.on_back_click()
            return

        # TODO: Set maximum image size and resize
        # TODO: Easier navigation - jump to other class, filenames listed down the side

        # match window size to the largest image in the directory
        width, height = 0, 0
        for f in filenames:
            image = Image.open(f)
            width, height = max(image.size[0], width), max(image.size[1], height)
        self.master.geometry(f"{width+100}x{height+200}")

        if 0 <= self.current_image_index < len(filenames):
            image_path = filenames[self.current_image_index]

            # set display label as filename
            self.label.config(text=os.path.split(image_path)[-1])
            image_label = os.path.normpath(image_path).split(os.path.sep)[-2]
            self.selected_option.set(image_label)


            image = Image.open(image_path)
            background = Image.new('RGBA', (width, height), (255, 255, 255, 255))
            offset = ((width - image.size[0]) // 2, (height - image.size[1]) // 2)
            background.paste(image, offset)
            photo_image = ImageTk.PhotoImage(background)
            self.image_label.configure(image=photo_image)
            self.image_label.image = photo_image

            if self.current_image_index == 0:
                self.prev_button.config(state="disabled")
                # If this is the last image, disable the 'Next' button
            elif self.current_image_index == len(filenames) - 1:
                self.next_button.config(state="disabled")
                # If this is not the first or last image, enable both buttons
            else:
                self.prev_button.config(state="normal")
                self.next_button.config(state="normal")

        else:
            self.image_label.configure(image=None)
            tk.messagebox.showinfo("Info", "No more images to display")

    def on_back_click(self):
        self.master.switch_frame(MainWindow)


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.geometry('500x500')
        self.switch_frame(MainWindow)

    def switch_frame(self, frame_class, *args):
        new_frame = frame_class(self, *args)
        if self.frame is not None:
            self.frame.destroy()
        self.frame = new_frame
        # self.frame.pack()
        self.frame.place(relx=0.5, rely=0.5, anchor='center')


app = MainApp()
app.mainloop()
