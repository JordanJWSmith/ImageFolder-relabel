import tkinter as tk
import tkinter.messagebox
from tkinter.ttk import *
from PIL import ImageTk, Image
import os

# TODO: take root directory from config.json file
root_dir = 'input'

# TODO: Move to function. Check for directory and issue error message if it doesn't exist
# dir_tree = {}
# for dir_path, dir_names, filenames in os.walk(root_dir):
#     parts = dir_path.split(os.sep)
#     curr = dir_tree
#     if len(dir_names):
#         for p in parts:
#             curr = curr.setdefault(p, {})
#     else:
#         for p in parts:
#             curr = curr.setdefault(p, [file for file in filenames])


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.configure(bg='white')
        self.dir_tree = {}

        self.build_dir_tree()

        for ix, _dir in enumerate(self.dir_tree[root_dir].keys()):
            self.button = tk.Button(self, text=_dir, command=lambda k=_dir: self.on_button_click(k))
            self.button.pack(side='left', padx=20)

        self.pack(side="top", fill="both", expand=True)

    def on_button_click(self, button_name):
        self.master.switch_frame(SecondWindow, button_name, self.dir_tree, self.build_dir_tree)

    def build_dir_tree(self):
        # print('before: ', self.dir_tree)
        dir_tree = {}
        for dir_path, dir_names, filenames in os.walk(root_dir):
            parts = dir_path.split(os.sep)
            curr = dir_tree
            if len(dir_names):
                for p in parts:
                    curr = curr.setdefault(p, {})
            else:
                for p in parts:
                    curr = curr.setdefault(p, [file for file in filenames])
        self.dir_tree = dir_tree
        # print('after:', self.dir_tree)


class SecondWindow(tk.Frame):
    def __init__(self, master=None, button_name=None, dir_tree=None, build_dir_tree=None):
        super().__init__(master)
        self.master = master
        self.dir_tree = dir_tree
        self.build_dir_tree = build_dir_tree
        self.button_name = button_name
        self.file_paths = [os.path.join(root_dir, button_name, cl) for cl in self.dir_tree[root_dir][button_name].keys()]
        self.current_image_index = 0
        self.processed_images = {}
        self.current_image = tk.StringVar()
        self.filenames = []

        self.get_filenames()

        self.configure(bg='white')

        self.root_frame = tk.Frame(self, bg='white')
        self.root_frame.pack()

        self.base_image_frame = tk.Frame(self.root_frame, bg='white')
        self.base_image_frame.pack(side='right')

        self.label = tk.Label(self.base_image_frame, font=('Helvetica', 12, 'bold'), bg='white')
        self.label.pack(side='top')

        # Create a label to display the image
        self.image_label = tk.Label(self.base_image_frame, bg='white')
        self.image_label.pack(side='top')

        self.button_frame = tk.Frame(self.base_image_frame, bg='white')
        self.button_frame.pack(side='bottom')

        # Create buttons to move to the next or previous image
        self.prev_button = tk.Button(self.button_frame, text="Previous", font=('Helvetica', 12),
                                     command=self.on_prev_click, bg='#555555', fg='white')
        self.prev_button.pack(side="left", padx=20, pady=20)

        self.next_button = tk.Button(self.button_frame, text="Next", font=('Helvetica', 12),
                                     command=self.on_next_click, bg='#555555', fg='white')
        self.next_button.pack(side="left", padx=20, pady=20)

        self.radio_frame = tk.Frame(self.base_image_frame, bg='white')
        self.radio_frame.pack(side='bottom')

        self.selected_option = tk.StringVar()
        self.selected_option.trace('w', self.on_option_change)

        # TODO: Add keyboard bindings to radio buttons and image navigation
        for ix, lab in enumerate(self.dir_tree[root_dir][button_name].keys()):
            self.option_radio = tk.Radiobutton(self.radio_frame, text=f'{ix+1}) {lab}', font=('Helvetica', 12),
                                               variable=self.selected_option, value=lab, pady=20, bg='white')
            self.option_radio.pack(side='left')

        # Create a frame to hold the Listbox widget
        self.list_frame = tk.Frame(self.root_frame, bg='white')
        self.list_frame.pack(side='left')

        self.back_button = tk.Button(self.root_frame, text="Main Menu", command=lambda: self.on_back_click(),
                                     bg='white', padx=5, pady=5)
        self.back_button.place(relx=0, rely=0, anchor='nw')

        self.chosen_dir_label = tk.Label(self.list_frame, text=os.path.join(self.button_name, ''),
                                         font=('Helvetica', 12), bg='white')
        self.chosen_dir_label.pack(side='top')

        # Create a Listbox widget and populate it with the filenames from the self.filenames list
        max_filename_length = max([len(os.path.join(os.path.basename(os.path.dirname(filename)),
                                                    os.path.basename(filename))) for filename in self.filenames])
        imlist_width = max(20, max_filename_length)
        self.image_list = tk.Listbox(self.list_frame, selectmode='single', width=imlist_width,
                                     font=('Helvetica', 12), relief='sunken', selectbackground='#008CBA')
        self.populate_image_list()

        # Bind a double click event to the Listbox widget
        self.image_list.bind('<Double-Button-1>', self.on_list_double_click)

        # Pack the Listbox widget
        self.image_list.pack(side='top')
        self.image_list.selection_set(self.current_image_index)

        self.submit_button_frame = tk.Frame(self.list_frame, bg='white')
        self.submit_button_frame.pack(side='bottom')

        self.submit_button = tk.Button(self.submit_button_frame, text='Submit', font=('Helvetica', 12, 'bold'),
                                       bg='#008CBA', fg='white', command=lambda: self.refactor_images())
        self.submit_button.pack(side="bottom", padx=20, pady=20)

        self.width, self.height = 0, 0
        for f in self.filenames:
            image = Image.open(f)
            self.width, self.height = max(image.size[0], self.width), max(image.size[1], self.height)
        self.master.geometry(f"{self.width + 400}x{self.height + 200}")
        self.image_list.configure(height=int(self.height / 21))

        # Display the first image
        self.display_images()
        self.pack()

    def on_list_double_click(self, event):
        selection = self.image_list.curselection()
        if not selection:
            return
        self.current_image_index = selection[0]
        self.display_images()

    def on_option_change(self, *args):
        if self.current_image.get():
            self.processed_images[self.current_image.get()] = self.selected_option.get()
            if os.path.basename(os.path.dirname(self.current_image.get())) != self.selected_option.get():
                print(f'index {self.current_image_index}: {os.path.basename(os.path.dirname(self.current_image.get()))} != {self.selected_option.get()}')
                self.image_list.itemconfigure(self.current_image_index, background="#D9F1FF")
            self.submit_button_state()

    def on_next_click(self):
        self.image_list.selection_clear(0, 'end')
        self.current_image_index += 1
        self.display_images()
        self.image_list.selection_set(self.current_image_index)
        self.image_list.see(self.current_image_index)

    def on_prev_click(self):
        self.image_list.selection_clear(0, 'end')
        self.current_image_index -= 1
        self.display_images()
        self.image_list.selection_set(self.current_image_index)
        self.image_list.see(self.current_image_index)

    def get_filenames(self):
        f_names = []
        try:
            for pathe in self.file_paths:
                f_names += [os.path.join(pathe, f) for f in os.listdir(pathe)
                            if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        except OSError:
            tk.messagebox.showerror("Error", "Invalid directory path")
            self.on_back_click()
            return
        self.filenames = f_names

    def refactor_images(self):
        for f_name, label in self.processed_images.items():
            if os.path.basename(os.path.dirname(f_name)) != label:
                try:
                    new_path = os.path.join(root_dir, self.button_name, label, os.path.basename(f_name))
                    print('refactoring:', f_name, '->',
                          os.path.join(root_dir, self.button_name, label, os.path.basename(f_name)))
                    os.rename(f_name, new_path)
                except Exception as e:
                    tk.messagebox.showinfo("Info", f'Error refactoring {f_name}. Error message:\n{e}')
        self.refresh_window()
        self.image_list.selection_clear(0, 'end')
        self.image_list.selection_set(self.current_image_index)
        self.image_list.see(self.current_image_index)

    def refresh_window(self):
        self.processed_images = {}
        self.build_dir_tree()
        self.build_filepaths()
        self.get_filenames()
        self.populate_image_list()
        self.display_images()

    def build_filepaths(self):
        self.file_paths = [os.path.join(root_dir, self.button_name, cl)
                           for cl in self.dir_tree[root_dir][self.button_name].keys()]

    def populate_image_list(self):
        self.image_list.delete(0, "end")
        for filename in self.filenames:
            filename_tail = os.path.join(os.path.basename(os.path.dirname(filename)), os.path.basename(filename))
            self.image_list.insert('end', filename_tail)

    def submit_button_state(self):
        for f_name, label in self.processed_images.items():
            if os.path.basename(os.path.dirname(f_name)) != label:
                self.submit_button.config(state="normal")
                return
        self.submit_button.config(state="disabled")

    def display_images(self):

        # TODO: Set maximum image size as a percentage of screen size and resize

        if 0 <= self.current_image_index < len(self.filenames):
            image_path = self.filenames[self.current_image_index]
            self.label.config(text=os.path.split(image_path)[-1])
            self.current_image.set(image_path)

            # set display label as filename
            if image_path in self.processed_images.keys():
                self.selected_option.set(self.processed_images[image_path])
            else:
                image_label = os.path.normpath(image_path).split(os.path.sep)[-2]
                self.selected_option.set(image_label)

            image = Image.open(image_path)
            background = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 255))
            offset = ((self.width - image.size[0]) // 2, (self.height - image.size[1]) // 2)
            background.paste(image, offset)
            photo_image = ImageTk.PhotoImage(background)
            self.image_label.configure(image=photo_image)
            self.image_label.image = photo_image

            if self.current_image_index == 0:
                self.prev_button.config(state="disabled")
                # If this is the last image, disable the 'Next' button
            elif self.current_image_index == len(self.filenames) - 1:
                print('index:', self.current_image_index, 'length filenames:', len(self.filenames))
                self.next_button.config(state="disabled")
                # If this is not the first or last image, enable both buttons
            else:
                self.prev_button.config(state="normal")
                self.next_button.config(state="normal")

        else:
            self.image_label.configure(image=None)
            tk.messagebox.showinfo("Info", "No more images to display")

        # print(self.processed_images)

    def on_back_click(self):
        self.master.switch_frame(MainWindow)


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.geometry('500x500')
        self.switch_frame(MainWindow)
        self.configure(bg='white')

    def switch_frame(self, frame_class, *args):
        new_frame = frame_class(self, *args)
        if self.frame is not None:
            self.frame.destroy()
        self.frame = new_frame
        # self.frame.pack()
        self.frame.place(relx=0.5, rely=0.5, anchor='center')


app = MainApp()
app.mainloop()
