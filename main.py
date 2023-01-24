import tkinter as tk
import tkinter.messagebox
import tkinter.ttk
import os
import json
from PIL import ImageTk, Image, ImageDraw
from web_scrape import generate_dataset

with open('input_dir.json', 'r') as f:
    input_json = json.load(f)
    root_dir = input_json['input_dir']

    if not root_dir:
        root_dir = 'input/'

if not os.path.exists(root_dir):
    print('Input directory not found.')
    choice = ''
    while choice.lower() not in ['y', 'n']:
        choice = input('Generate webscraped dataset? y/n: ')
        if choice.lower() == 'y':
            generate_dataset()


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.configure(bg='white')
        self.dir_folders = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

        if not len(self.dir_folders):
            msg = "No subdirectories detected.\n" \
                  "Please add directories containing image sets for training, validation, etc"
            tk.messagebox.showerror("Error", msg)
            app.destroy()

        self.instructions = tk.Label(self, text='Select a directory to view', font=('Helvetica', 14), bg='white')
        self.instructions.pack(side='top', pady=30)

        for dir_button in self.dir_folders:
            self.button = tk.Button(self, text=dir_button, command=lambda k=dir_button: self.on_button_click(k),
                                    font=('Helvetica', 12))
            self.button.pack(side='top', padx=20, pady=10)

        self.pack(side="top", fill="both", expand=True)

    def on_button_click(self, button_name):
        root_and_dir = os.path.join(root_dir, button_name)
        self.master.switch_frame(SecondWindow, self.dir_folders, root_and_dir)


class SecondWindow(tk.Frame):
    def __init__(self, master=None, dir_folders=None, root_and_dir=None):
        super().__init__(master)
        self.master = master
        self.root_and_dir = root_and_dir
        self.dir_folders = dir_folders
        self.file_paths = [os.path.join(self.root_and_dir, f) for f in os.listdir(self.root_and_dir)]
        self.current_image_index = 0
        self.processed_images = {}
        self.current_image = tk.StringVar()
        self.filenames = []
        self.image = None
        self.bounding_boxes = {}
        self.master.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.get_filenames()
        self.get_bounding_boxes()

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

        self.image_label.bind("<ButtonPress-1>", self.bb_on_press)
        self.image_label.bind("<B1-Motion>", self.bb_on_motion)
        self.image_label.bind("<ButtonRelease-1>", self.bb_on_release)
        self.image_label.bind("<Motion>", self.on_enter)

        self.start_x, self.start_y = None, None
        self.rect = None

        self.button_frame = tk.Frame(self.base_image_frame, bg='white')
        self.button_frame.pack(side='bottom')

        # Create buttons to move to the next or previous image
        left_icon = tk.PhotoImage(file="icons/nav/left.png").subsample(14, 14)
        self.prev_button = tk.Button(self.button_frame, image=left_icon, command=self.on_prev_click,
                                     height=50, width=50, bg='white')
        self.prev_button.image = left_icon
        self.prev_button.pack(side="left", padx=30, pady=20)

        right_icon = tk.PhotoImage(file="icons/nav/right.png").subsample(14, 14)
        self.next_button = tk.Button(self.button_frame, image=right_icon, command=self.on_next_click,
                                     height=50, width=50, bg='white')
        self.next_button.image = right_icon
        self.next_button.pack(side="left", padx=30, pady=20)

        self.radio_frame = tk.Frame(self.base_image_frame, bg='white')
        self.radio_frame.pack(side='bottom')

        self.separator = tk.ttk.Separator(self.radio_frame, orient='horizontal')
        self.separator.pack(fill='x')

        self.selected_option = tk.StringVar()
        self.selected_option.trace('w', self.on_option_change)

        # TODO: Dynamically resize window to fit labels?
        for ix, lab in enumerate(os.listdir(self.root_and_dir)):
            self.option_frame = tk.Frame(self.radio_frame, bg='white', padx=20)
            self.option_frame.pack(side='left')
            number_icon = tk.PhotoImage(file=f"icons/numbers/icons8-{ix+1}-100.png").subsample(2, 2)
            self.test_icon = tk.Label(self.option_frame, image=number_icon, bg='white')
            self.test_icon.image = number_icon
            self.test_icon.pack(side="left")
            self.option_radio = tk.Radiobutton(self.option_frame, text=f"{lab}", font=('Helvetica', 12),
                                               variable=self.selected_option, value=lab, pady=20, bg='white',)
            self.option_radio.pack(side='left')

        # key bindings won't work with >9 classes
        if len(os.listdir(self.root_and_dir)) < 10:
            self.master.bind("<Key>", self.on_key_press)

        # Create a frame to hold the Listbox widget
        self.list_frame = tk.Frame(self.root_frame, bg='white')
        self.list_frame.pack(side='left')

        back_icon = tk.PhotoImage(file="icons/nav/back.png").subsample(20, 20)
        self.back_button = tk.Button(self.root_frame, image=back_icon, command=lambda: self.on_back_click(),
                                     height=40, width=40, bg='white')
        self.back_button.image = back_icon
        self.back_button.place(relx=0, rely=0, anchor='nw')

        self.clear_bboxes_button = tk.Button(self.root_frame, text='Clear BBoxes', bg='white',
                                      command=self.clear_bboxes)
        self.clear_bboxes_button.place(relx=0.1, rely=0, anchor='nw')

        dir_label = os.path.join(os.path.basename(self.root_and_dir), '')
        self.chosen_dir_label = tk.Label(self.list_frame, text=dir_label,
                                         font=('Helvetica', 12), bg='white')
        self.chosen_dir_label.pack(side='top')

        # Create a Listbox widget and populate it with the filenames from the self.filenames list
        max_filename_length = max([len(os.path.join(os.path.basename(os.path.dirname(filename)),
                                                    os.path.basename(filename))) for filename in self.filenames])
        image_list_width = max(20, max_filename_length)
        self.image_list = tk.Listbox(self.list_frame, selectmode='single', width=image_list_width,
                                     font=('Helvetica', 12), relief='sunken', selectbackground='#008CBA')
        self.populate_image_list()

        # Bind a double click event to the Listbox widget
        self.image_list.bind('<Double-Button-1>', self.on_list_double_click)

        # Pack the Listbox widget
        self.image_list.pack(side='top')
        self.image_list.selection_set(self.current_image_index)

        self.submit_button_frame = tk.Frame(self.list_frame, bg='white')
        self.submit_button_frame.pack(side='bottom')

        # TODO: Modal with 'refactor [x] images? confirmation'
        self.submit_button = tk.Button(self.submit_button_frame, text='Relabel', font=('Helvetica', 12, 'bold'),
                                       bg='#008CBA', fg='white', command=lambda: self.refactor_images())
        self.submit_button.pack(side="bottom", padx=20, pady=20)

        self.width, self.height = 0, 0
        for f in self.filenames:
            image = Image.open(f)
            self.width, self.height = max(image.size[0], self.width), max(image.size[1], self.height)
        self.master.geometry(f"{self.width + 400}x{self.height + 200}")
        self.image_list.configure(height=int(self.height / 21))
        self.image_label.configure(height=self.height, width=self.width)

        # Display the first image
        self.display_images()
        self.pack()

    # TODO: Ability to remove individual bounding boxes

    def get_bounding_boxes(self):
        bbox_f = open('bounding_boxes.json')
        self.bounding_boxes = json.load(bbox_f)

    def bb_on_press(self, event):
        img_x = event.x - (self.width - self.image.width) // 2
        img_y = event.y - (self.height - self.image.height) // 2
        if 0 < img_x <= self.image.width and 0 < img_y <= self.image.height:
            self.display_images()
            self.start_x, self.start_y = img_x, img_y

    def bb_on_motion(self, event):
        img_x = event.x - (self.width - self.image.width) // 2
        img_y = event.y - (self.height - self.image.height) // 2
        if self.start_x is not None and self.start_y is not None \
                and 0 < img_x <= self.image.width and 0 < img_y <= self.image.height:
            if self.rect:
                self.display_images()

            self.rect = (self.start_x, self.start_y, img_x, img_y)
            self.draw.rectangle(xy=self.rect, outline="red")
            self.photo_image = ImageTk.PhotoImage(self.image)
            self.image_label.configure(image=self.photo_image)

    def bb_on_release(self, event):
        img_x = event.x - (self.width - self.image.width) // 2
        img_y = event.y - (self.height - self.image.height) // 2
        if 0 < img_x <= self.image.width and 0 < img_y <= self.image.height and self.start_x and self.start_y:
            end_x, end_y = img_x, img_y

            # sort bbox coords so they always start in top left
            sorted_xs = sorted([self.start_x, end_x])
            sorted_ys = sorted([self.start_y, end_y])
            # bbox = [self.start_x, self.start_y, end_x, end_y]
            bbox = [sorted_xs[0], sorted_ys[0], sorted_xs[1], sorted_ys[1]]

            min_bbox_size = 10
            if abs(self.start_x - end_x) > min_bbox_size and abs(self.start_y - end_y) > min_bbox_size:
                if self.current_image.get() in self.bounding_boxes.keys():
                    self.bounding_boxes[self.current_image.get()].append(bbox)
                else:
                    self.bounding_boxes[self.current_image.get()] = [bbox]

            # self.write_bboxes()

            print(self.bounding_boxes)
            self.display_images()
            self.start_x, self.start_y = None, None
            self.rect = None

    def write_bboxes(self):
        json_object = json.dumps(self.bounding_boxes, indent=4)
        with open("bounding_boxes.json", "w") as outfile:
            outfile.write(json_object)

    def clear_bboxes(self):
        del self.bounding_boxes[self.current_image.get()]
        self.display_images()

    # def remove_bbox(self, xy):
    #     print('removing', xy, 'from', self.bounding_boxes[self.current_image.get()])
    #     self.bounding_boxes[self.current_image.get()].remove(xy)
    #     self.display_images()

    def on_enter(self, event):
        if self.current_image.get() in self.bounding_boxes.keys():
            img_x = event.x - (self.width - self.image.width) // 2
            img_y = event.y - (self.height - self.image.height) // 2
            bboxes = self.bounding_boxes[self.current_image.get()]
            for bbox in bboxes:
                if bbox[0] <= img_x <= bbox[2] and bbox[1] <= img_y <= bbox[3]:
                    print('within bbox', bbox)

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
                self.image_list.itemconfigure(self.current_image_index, background="#D9F1FF")
            else:
                self.image_list.itemconfigure(self.current_image_index, background="#FFFFFF")
            self.submit_button_state()

    def on_next_click(self):
        self.image_list.selection_clear(0, 'end')
        self.current_image_index += 1
        self.display_images()
        self.image_list.selection_set(self.current_image_index)
        self.image_list.see(self.current_image_index)
        self.start_x, self.start_y = None, None
        self.rect = None

    def on_prev_click(self):
        self.image_list.selection_clear(0, 'end')
        self.current_image_index -= 1
        self.display_images()
        self.image_list.selection_set(self.current_image_index)
        self.image_list.see(self.current_image_index)
        self.start_x, self.start_y = None, None
        self.rect = None

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
                    new_path = os.path.join(self.root_and_dir, label, os.path.basename(f_name))
                    print('refactoring:', f_name, '->',
                          os.path.join(self.root_and_dir, label, os.path.basename(f_name)))
                    os.rename(f_name, new_path)
                except Exception as e:
                    tk.messagebox.showinfo("Info", f'Error refactoring {f_name}. Error message:\n{e}')
        self.refresh_window()
        self.image_list.selection_clear(0, 'end')
        self.image_list.selection_set(self.current_image_index)
        self.image_list.see(self.current_image_index)

    def refresh_window(self):
        self.processed_images = {}
        self.build_filepaths()
        self.get_filenames()
        self.populate_image_list()
        self.display_images()

    def build_filepaths(self):
        self.file_paths = [os.path.join(self.root_and_dir, f) for f in os.listdir(self.root_and_dir)]

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

    def on_key_press(self, event):
        str_nums = [str(i) for i in range(10)]
        next_image_key = ['Right', 'Down']
        prev_image_key = ['Left', 'Up']

        # key bindings to select radio button
        if event.keysym in str_nums:
            for ix, lab in enumerate(os.listdir(self.root_and_dir)):
                if event.char == str(ix+1):
                    self.selected_option.set(lab)

        # key bindings to move through images
        elif event.keysym in next_image_key:
            if self.current_image_index != len(self.filenames) - 1:
                self.on_next_click()
        elif event.keysym in prev_image_key:
            if self.current_image_index != 0:
                self.on_prev_click()

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

            self.image = Image.open(image_path)
            self.draw = ImageDraw.Draw(self.image)

            if image_path in self.bounding_boxes.keys():
                self.clear_bboxes_button.config(state="normal")
                for xy in self.bounding_boxes[image_path]:
                    self.draw.rectangle(xy=xy, outline="red")

                    # add remove button
                    # self.remove_bbox_button = tk.Button(self.image_label, text='x', command=lambda: self.remove_bbox(xy))
                    # translated_x = xy[2] + (self.width - self.image.width) // 2
                    # translated_y = xy[1] + (self.height - self.image.height) // 2
                    # self.remove_bbox_button.place(x=translated_x, y=translated_y)
            else:
                self.clear_bboxes_button.config(state="disabled")

            photo_image = ImageTk.PhotoImage(self.image)

            self.image_label.configure(image=photo_image)
            self.image_label.image = photo_image

            if self.current_image_index == 0:
                self.prev_button.config(state="disabled")
            elif self.current_image_index == len(self.filenames) - 1:
                self.next_button.config(state="disabled")
            else:
                self.prev_button.config(state="normal")
                self.next_button.config(state="normal")

        else:
            self.image_label.configure(image=None)
            tk.messagebox.showinfo("Info", "No more images to display")

    def on_back_click(self):
        self.write_bboxes()
        self.master.switch_frame(MainWindow)

    def exit_app(self):
        self.write_bboxes()
        app.destroy()


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
        self.frame.place(relx=0.5, rely=0.5, anchor='center')


if __name__ == '__main__':
    app = MainApp()
    app.title('ImageFolder-relabel')
    app.mainloop()
