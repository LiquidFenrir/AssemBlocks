# Python 3.7+, relies on the new dict behavior

import os, sys
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from json import dump, load, dumps, loads
from copy import copy
import traceback
from PIL.ImageTk import PhotoImage as PNGImage

IMAGE_FOLDER = "images"
DEFAULT_FOLDER = "/"

MIN_STACK_SIZE = 1
MAX_STACK_SIZE = 255
MIN_MEMORY_SIZE = 1
MAX_MEMORY_SIZE = 255
MIN_SUBPROGRAMS = 1
MAX_SUBPROGRAMS = 6

MAX_TESTS = 13

MAX_GRID_SIZE = 18
PIXELS_PER_SQUARE = 16

images = {}
SQUARE_TYPES = (
    "square_empty",
    "square_marked",
    "square_painted",
    "square_circle",
    "square_circle_hole",
    "square_circle_hole_filled",
    "square_square",
    "square_square_hole",
    "square_square_hole_filled",
    "square_triangle",
    "square_triangle_hole",
    "square_triangle_hole_filled",
)

class Catcher: 
    def __init__(self, func, subst, widget):
        self.func = func 
        self.subst = subst
        self.widget = widget

    def __call__(self, *args):
        try:
            if self.subst:
                args = self.subst(*args)
            return self.func(*args)
        except SystemExit as msg:
            raise SystemExit from msg
        except Exception as e:
            error = traceback.extract_tb(sys.exc_info()[2])[-1]
            messagebox.showerror("AssemBlocks error", "An error occured at line {}: {}\n\n{}\nPlease report this to the creator of the application with a description of what you were doing at the time.".format(error.lineno, error.line, "\n".join(err for err in traceback.format_exception_only(type(e), e))))

class AssemBlocksTest:
    def __init__(self, test):
        self.width = test["width"]
        self.height = test["height"]

        self.robot_column = test["robot_column"]
        self.robot_row = test["robot_row"]

        self.grid_start = [copy(row) + ["square_empty"] * (MAX_GRID_SIZE-len(row)) for row in test["grid_start"]]
        if len(self.grid_start) != MAX_GRID_SIZE:
            self.grid_start += [["square_empty" for x in range(MAX_GRID_SIZE)] for y in range(MAX_GRID_SIZE - len(self.grid_start))]

        self.grid_wanted = [copy(row) + ["square_empty"] * (MAX_GRID_SIZE-len(row)) for row in test["grid_wanted"]]
        if len(self.grid_wanted) != MAX_GRID_SIZE:
            self.grid_wanted += [["square_empty" for x in range(MAX_GRID_SIZE)] for y in range(MAX_GRID_SIZE - len(self.grid_wanted))]

    def draw(self, grid, canvas, draw_robot):
        canvas.delete("grid")
        for y, row in enumerate(grid[:self.height]):
            for x, square in enumerate(row[:self.width]):
                if type(square) is int:
                    canvas.create_image(x * PIXELS_PER_SQUARE, y * PIXELS_PER_SQUARE, anchor=tk.NW, image=images["square_empty"], tags="grid")
                    canvas.create_text(x * PIXELS_PER_SQUARE, y * PIXELS_PER_SQUARE, anchor=tk.NW, text=str(square), tags="grid")
                else:
                    canvas.create_image(x * PIXELS_PER_SQUARE, y * PIXELS_PER_SQUARE, anchor=tk.NW, image=images[square], tags="grid")

        if draw_robot:
            canvas.coords("robot", (self.robot_column * PIXELS_PER_SQUARE, self.robot_row * PIXELS_PER_SQUARE))
            canvas.tag_raise("robot")

    def draw_start(self, canvas):
        self.draw(self.grid_start, canvas, True)

    def draw_wanted(self, canvas):
        self.draw(self.grid_wanted, canvas, False)

    def set_square(self, grid, x, y, square):
        grid[y][x] = square

    def set_start_square(self, x, y, square):
        self.set_square(self.grid_start, x, y, square)

    def set_wanted_square(self, x, y, square):
        self.set_square(self.grid_wanted, x, y, square)

    def get(self):
        grid_start = [row[:self.width] for row in self.grid_start[:self.height]]
        grid_wanted = [row[:self.width] for row in self.grid_wanted[:self.height]]
        return {
            "width": self.width,
            "height": self.height,
            "robot_column": self.robot_column,
            "robot_row": self.robot_row,
            "grid_start": grid_start,
            "grid_wanted": grid_wanted,
        }

BASIC_TEST = {
    "width": MAX_GRID_SIZE//2,
    "height": MAX_GRID_SIZE//2,
    "robot_column": 0,
    "robot_row": 0,
    "grid_start" : [["square_empty" for x in range(MAX_GRID_SIZE)] for y in range(MAX_GRID_SIZE)],
    "grid_wanted" : [["square_empty" for x in range(MAX_GRID_SIZE)] for y in range(MAX_GRID_SIZE)]
}

BASIC_LEVEL = {
    "info": {
        "title": "",
        "description": "",
    },
    "mission": "",
    "grid_coords": False,
    "limitations": {
        "stack_size": 0,
        "memory_size": 0,
        "subprograms": 0,
        "disabled": []
    },
    "tests": [
        AssemBlocksTest(BASIC_TEST).get()
    ]
}

class Application():
    def on_closing(self):
        if self.update_level_data():
            self.ask_for_saving("quitting")

        if messagebox.askokcancel("AssemBlocks level editor", "The application will be closed."):
            self.root.destroy()

    def open_level(self):
        if self.update_level_data():
            self.ask_for_saving("opening a new file")

        initial_folder = DEFAULT_FOLDER if self.filename is None else os.path.dirname(self.filename)
        new_filename = filedialog.askopenfilename(initialdir=initial_folder, title="Select level to open", filetypes = (("AssemBlocks level file","*.json"),))
        if new_filename is not None and len(new_filename) != 0:
            self.filename = new_filename
            with open(self.filename) as f:
                self.level_data = load(f)
                self.load_level_data()

    def open_level_from_clipboard(self):
        if self.update_level_data():
            self.ask_for_saving("loading from clipboard")

        new_level_data = loads(self.root.clipboard_get())
        self.level_data = new_level_data
        self.load_level_data()

    def ask_for_saving(self, what_next):
        if messagebox.askyesno("AssemBlocks level editor", "Do you want to save the current level before " + what_next + "?"):
            self.save_level(False)

    def save_level(self, ask_for_filename):
        if self.filename is None:
            ask_for_filename = True

        if ask_for_filename:
            initial_folder = DEFAULT_FOLDER if self.filename is None else os.path.dirname(self.filename)
            new_filename = filedialog.asksaveasfilename(initialdir=initial_folder, title="Select file to save level to", filetypes = (("AssemBlocks level file","*.json"),))
            if new_filename is None or len(new_filename) == 0:  # Cancelled
                return

            self.filename = new_filename

        with open(self.filename, "w") as f:
            self.update_level_data()
            dump(self.level_data, f, sort_keys=True, indent=4)

    def save_level_to_clipboard(self):
        # self.save_level()
        self.update_level_data()
        self.root.clipboard_clear()
        self.root.clipboard_append(dumps(self.level_data))

    def about(self):
        messagebox.showinfo("AssemBlocks level editor", "AssemBlocks and the AssemBlocks level editor were made by LiquidFenrir (https://github.com/LiquidFenrir) and are licensed under the GPLv3")

    def add_tab(self, notebook, tab_name: str, character_to_underline: int = -1):
        frame = tk.Frame(notebook)
        if character_to_underline == -1:
            notebook.add(frame, text=tab_name)
        else:
            notebook.add(frame, text=tab_name, underline=character_to_underline)
        return frame

    def init_meta(self):
        self.meta_frame = self.add_tab(self.notebook, "Metadata", 0)

        self.info_labelframe = tk.LabelFrame(self.meta_frame, text="Info")
        self.info_labelframe.grid(row=0, column=0, sticky="NWSE")

        self.title_label = tk.Label(self.info_labelframe, text="Title")
        self.title_label.grid(row=0, column=0, sticky="NWSE")
        self.title_text = tk.Text(self.info_labelframe, wrap=tk.WORD, height=1, width=51)
        self.title_text.grid(row=0, column=1, sticky="NWSE")

        self.description_label = tk.Label(self.info_labelframe, text="Description")
        self.description_label.grid(row=1, column=0, sticky="NWSE")
        self.description_text = tk.Text(self.info_labelframe, wrap=tk.WORD, spacing3=2, height=2, width=47)
        self.description_text.grid(row=1, column=1, sticky="NWSE")

        self.mission_labelframe = tk.LabelFrame(self.meta_frame, text="Mission")
        self.mission_labelframe.grid(row=1, column=0, sticky="NWSE")

        self.mission_text = tk.Text(self.mission_labelframe, wrap=tk.WORD, spacing3=2, height=8, width=78)
        self.mission_text.grid(row=0, column=0, sticky="NWSE")

        self.grid_coords_labelframe = tk.LabelFrame(self.meta_frame, text="Grid coordinates")
        self.grid_coords_labelframe.grid(row=2, column=0, sticky="NWSE")

        self.grid_coords_var = tk.IntVar()
        self.grid_coords_var.set(int(self.level_data["grid_coords"]))
        self.grid_coords_labelframe.grid_columnconfigure(0, uniform="grid_coords_labelframe")
        self.grid_coords_labelframe.grid_columnconfigure(1, uniform="grid_coords_labelframe")
        self.grid_coords_hidden = tk.Radiobutton(self.grid_coords_labelframe, text="Hidden", variable=self.grid_coords_var, value=int(False), command=self.toggle_grid_coords)
        self.grid_coords_shown = tk.Radiobutton(self.grid_coords_labelframe, text="Shown", variable=self.grid_coords_var, value=int(True), command=self.toggle_grid_coords)

        self.grid_coords_hidden.grid(row=0, column=0, sticky="NWSE")
        self.grid_coords_shown.grid(row=0, column=1, sticky="NWSE")

        self.limitations_labelframe = tk.LabelFrame(self.meta_frame, text="Limitations")
        self.limitations_labelframe.grid(row=3, column=0, sticky="NWSE")

        self.stack_size_label = tk.Label(self.limitations_labelframe, text="Stack size")
        self.stack_size_label.grid(row=0, column=0, sticky="NWSE")
        self.stack_allowed_var = tk.IntVar()
        self.stack_allowed_var.set(int(False))
        self.stack_allowed_checkbutton = tk.Checkbutton(self.limitations_labelframe, text="Allow stack", onvalue=int(True), offvalue=int(False), var=self.stack_allowed_var, command=self.toggle_stack_allowed)
        self.stack_allowed_checkbutton.grid(row=0, column=1, sticky="NWSE")
        self.stack_size_var = tk.StringVar()
        self.stack_size_spinbox = tk.Spinbox(self.limitations_labelframe, from_=MIN_STACK_SIZE, to=MAX_STACK_SIZE, textvariable=self.stack_size_var, state=tk.DISABLED, justify=tk.RIGHT)
        self.stack_size_spinbox.grid(row=0, column=2, sticky="NWSE")

        self.memory_size_label = tk.Label(self.limitations_labelframe, text="Memory size")
        self.memory_size_label.grid(row=1, column=0, sticky="NWSE")
        self.memory_allowed_var = tk.IntVar()
        self.memory_allowed_var.set(int(False))
        self.memory_allowed_checkbutton = tk.Checkbutton(self.limitations_labelframe, text="Allow memory", onvalue=int(True), offvalue=int(False), var=self.memory_allowed_var, command=self.toggle_memory_allowed)
        self.memory_allowed_checkbutton.grid(row=1, column=1, sticky="NWSE")
        self.memory_size_var = tk.StringVar()
        self.memory_size_spinbox = tk.Spinbox(self.limitations_labelframe, from_=MIN_MEMORY_SIZE, to=MAX_MEMORY_SIZE, textvariable=self.memory_size_var, state=tk.DISABLED, justify=tk.RIGHT)
        self.memory_size_spinbox.grid(row=1, column=2, sticky="NWSE")

        self.subprograms_count_label = tk.Label(self.limitations_labelframe, text="Subprograms")
        self.subprograms_count_label.grid(row=2, column=0, sticky="NWSE")
        self.subprograms_allowed_var = tk.IntVar()
        self.subprograms_allowed_var.set(int(False))
        self.subprograms_allowed_checkbutton = tk.Checkbutton(self.limitations_labelframe, text="Allow subprograms", onvalue=int(True), offvalue=int(False), var=self.subprograms_allowed_var, command=self.toggle_subprograms_allowed)
        self.subprograms_allowed_checkbutton.grid(row=2, column=1, sticky="NWSE")
        self.subprograms_count_var = tk.StringVar()
        self.subprograms_count_spinbox = tk.Spinbox(self.limitations_labelframe, from_=MIN_SUBPROGRAMS, to=MAX_SUBPROGRAMS, textvariable=self.subprograms_count_var, state=tk.DISABLED, justify=tk.RIGHT)
        self.subprograms_count_spinbox.grid(row=2, column=2, sticky="NWSE")

        self.banned_commands = tk.Label(self.limitations_labelframe, text="Banned commands")
        self.banned_commands.grid(row=3, rowspan=2, column=0, sticky="NWSE")
        self.banned_commands_text = tk.Text(self.limitations_labelframe, wrap=tk.WORD, spacing3=2, height=4, width=64)
        self.banned_commands_text.grid(row=3, rowspan=2, column=1, columnspan=2, sticky="NWSE")

    def set_test_spawn_column(self):
        self.selected_test.robot_column = int(self.test_spawn_column_var.get()) - 1
        self.draw_test()

    def set_test_spawn_row(self):
        self.selected_test.robot_row = int(self.test_spawn_row_var.get()) - 1
        self.draw_test()

    def set_test_width(self):
        self.selected_test.width = int(self.test_width_var.get())
        self.draw_test()

    def set_test_height(self):
        self.selected_test.height = int(self.test_height_var.get())
        self.draw_test()

    def editor_selector_handler_radio(self):
        self.selected_square_type = self.selected_square_type_var.get()

    def editor_selector_handler_label(self, num):
        self.selected_square_type_var.set(num)
        self.selected_square_type = num

    def editor_handler(self, x, y, grid_setter):
        if x >= self.selected_test.width or y >= self.selected_test.height:
            return

        if self.selected_square_type == len(SQUARE_TYPES):
            square = int(self.square_number_value_var.get())
        else:
            square = SQUARE_TYPES[self.selected_square_type]

        grid_setter(x, y, square)
        self.draw_test()

    def editor_start_handler(self, event):
        self.editor_handler(event.x//PIXELS_PER_SQUARE, event.y//PIXELS_PER_SQUARE, self.selected_test.set_start_square)

    def editor_wanted_handler(self, event):
        self.editor_handler(event.x//PIXELS_PER_SQUARE, event.y//PIXELS_PER_SQUARE, self.selected_test.set_wanted_square)

    def init_tests(self):
        self.tests = []

        self.tests_frame = self.add_tab(self.notebook, "Tests", 0)
        self.tests_list_frame = tk.Frame(self.tests_frame)
        self.tests_list_frame.grid(row=0, column=0, sticky="NWSE")

        self.tests_list = tk.Listbox(self.tests_list_frame, width=len("Test XXX"), height=MAX_TESTS, selectmode=tk.SINGLE)
        self.tests_list.grid(row=1, column=0, columnspan=2, sticky="NWSE")
        self.tests_list.bind("<<ListboxSelect>>", self.select_test)
        self.tests_list.bind("<Double-Button-1>", self.select_test)

        self.add_test_button = tk.Button(self.tests_list_frame, text="Add test", command=self.add_test)
        self.add_test_button.grid(row=0, column=0, sticky="NWSE")
        self.delete_test_button = tk.Button(self.tests_list_frame, text="Delete last test", command=self.remove_test)
        self.delete_test_button.grid(row=0, column=1, sticky="NWSE")

        self.tests_display_frame = tk.Frame(self.tests_frame)
        self.tests_display_frame.grid(row=0, column=1, sticky="NWSE")

        self.test_meta_frame = tk.Frame(self.tests_display_frame)
        self.test_meta_frame.grid(row=0, column=0, columnspan=len(SQUARE_TYPES)+1, sticky="NWSE")
        self.test_width_var = tk.StringVar()
        self.test_height_var = tk.StringVar()
        self.test_spawn_column_var = tk.StringVar()
        self.test_spawn_row_var = tk.StringVar()

        self.test_width_label = tk.Label(self.test_meta_frame, text="Test width")
        self.test_width_label.grid(row=0, column=0, columnspan=2, sticky="NWSE")
        self.test_width_spinbox = tk.Spinbox(self.test_meta_frame, from_=1, to=MAX_GRID_SIZE, textvariable=self.test_width_var, width=3, command=self.set_test_width, justify=tk.RIGHT)
        self.test_width_spinbox.grid(row=0, column=2, columnspan=2, sticky="NWSE")

        self.test_height_label = tk.Label(self.test_meta_frame, text="Test height")
        self.test_height_label.grid(row=0, column=4, columnspan=2, sticky="NWSE")
        self.test_height_spinbox = tk.Spinbox(self.test_meta_frame, from_=1, to=MAX_GRID_SIZE, textvariable=self.test_height_var, width=3, command=self.set_test_height, justify=tk.RIGHT)
        self.test_height_spinbox.grid(row=0, column=6, columnspan=2, sticky="NWSE")

        self.test_spawn_column_label = tk.Label(self.test_meta_frame, text="Spawn column")
        self.test_spawn_column_label.grid(row=0, column=8, columnspan=2, sticky="NWSE")
        self.test_spawn_column_spinbox = tk.Spinbox(self.test_meta_frame, from_=1, to=MAX_GRID_SIZE, textvariable=self.test_spawn_column_var, width=3, command=self.set_test_spawn_column, justify=tk.RIGHT)
        self.test_spawn_column_spinbox.grid(row=0, column=10, columnspan=2, sticky="NWSE")

        self.test_spawn_row_label = tk.Label(self.test_meta_frame, text="Spawn row")
        self.test_spawn_row_label.grid(row=0, column=12, columnspan=2, sticky="NWSE")
        self.test_spawn_row_spinbox = tk.Spinbox(self.test_meta_frame, from_=1, to=MAX_GRID_SIZE, textvariable=self.test_spawn_row_var, width=3, command=self.set_test_spawn_row, justify=tk.RIGHT)
        self.test_spawn_row_spinbox.grid(row=0, column=14, columnspan=2, sticky="NWSE")

        self.selected_square_type_var = tk.IntVar()
        self.selected_square_type = 0
        self.selected_square_type_var.set(self.selected_square_type)

        self.selected_square_frames = []
        self.selected_square_labels = []
        self.selected_square_radios = []

        for i, square_type in enumerate(SQUARE_TYPES):
            self.selected_square_frames.append(tk.Frame(self.tests_display_frame))
            self.selected_square_labels.append(tk.Label(self.selected_square_frames[-1], image=images[square_type]))
            self.selected_square_radios.append(tk.Radiobutton(self.selected_square_frames[-1], variable=self.selected_square_type_var, value=i, command=self.editor_selector_handler_radio))

            self.selected_square_frames[-1].grid(row=1, column=i, sticky="NWSE")

            def handler(event, self=self, i=i):
                return self.editor_selector_handler_label(i)

            self.selected_square_labels[-1].bind("<Button-1>", handler)
            self.selected_square_labels[-1].grid(row=0, column=0, sticky="NWSE")
            self.selected_square_radios[-1].grid(row=1, column=0, sticky="NWSE")

        self.square_number_value_var = tk.StringVar()
        self.square_number_value_var.set("0")

        self.selected_square_frames.append(tk.Frame(self.tests_display_frame))
        self.selected_square_labels.append(tk.Spinbox(self.selected_square_frames[-1], from_=-99, to=99, textvariable=self.square_number_value_var, width=3, command=lambda: self.editor_selector_handler_label(len(SQUARE_TYPES)), justify=tk.RIGHT))
        self.selected_square_radios.append(tk.Radiobutton(self.selected_square_frames[-1], variable=self.selected_square_type_var, value=len(SQUARE_TYPES), command=self.editor_selector_handler_radio))

        self.selected_square_frames[-1].grid(row=1, column=len(SQUARE_TYPES), sticky="NWSE")
        self.selected_square_labels[-1].bind("<Button-1>", lambda ev: self.editor_selector_handler_label(len(SQUARE_TYPES)))
        self.selected_square_labels[-1].grid(row=0, column=0, sticky="NWSE")
        self.selected_square_radios[-1].grid(row=1, column=0, sticky="NWSE")

        self.tests_notebook = ttk.Notebook(self.tests_display_frame)
        self.tests_notebook.grid(row=2, column=0, columnspan=len(SQUARE_TYPES)+1, sticky="NWSE")

        self.tests_start_frame = self.add_tab(self.tests_notebook, "Start")
        self.tests_wanted_frame = self.add_tab(self.tests_notebook, "Wanted")

        self.tests_canvas_start = tk.Canvas(self.tests_start_frame, width=MAX_GRID_SIZE*PIXELS_PER_SQUARE, height=MAX_GRID_SIZE*PIXELS_PER_SQUARE)
        self.tests_canvas_start.grid(row=1, column=0, sticky="NWSE")
        self.tests_canvas_start.create_image(0,0, anchor=tk.NW, image=images["robot"], tags="robot")
        self.tests_canvas_start.bind("<Button-1>", self.editor_start_handler)

        self.tests_canvas_wanted = tk.Canvas(self.tests_wanted_frame, width=MAX_GRID_SIZE*PIXELS_PER_SQUARE, height=MAX_GRID_SIZE*PIXELS_PER_SQUARE)
        self.tests_canvas_wanted.grid(row=1, sticky="NWSE")
        self.tests_canvas_wanted.bind("<Button-1>", self.editor_wanted_handler)

    def __init__(self, root):
        self.root = root
        self.filename = None
        self.level_data = BASIC_LEVEL

        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=False)
        self.filemenu.add_command(label="Open", command=self.open_level)
        self.filemenu.add_command(label="Save", command=lambda: self.save_level(False))
        self.filemenu.add_command(label="Save As", command=lambda: self.save_level(True))
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.level_io = tk.Menu(self.menubar, tearoff=False)
        self.level_io.add_command(label="Export to clipboard", command=self.save_level_to_clipboard)
        self.level_io.add_command(label="Import from clipboard", command=self.open_level_from_clipboard)
        self.menubar.add_cascade(label="Clipboard", menu=self.level_io)

        self.menubar.add_command(label="About", command=self.about)

        self.root.config(menu=self.menubar)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.enable_traversal()
        self.notebook.grid(row=0, column=0, sticky="NWSE")

        self.init_meta()
        self.init_tests()

        self.load_level_data()

    def update_level_data(self):
        stack_size = 0 if not bool(self.stack_allowed_var.get()) else int(self.stack_size_var.get())
        if stack_size != 0:
            if stack_size > MAX_STACK_SIZE:
                stack_size = MAX_STACK_SIZE
            elif stack_size < MIN_STACK_SIZE:
                stack_size = MIN_STACK_SIZE

        memory_size = 0 if not bool(self.memory_allowed_var.get()) else int(self.memory_size_var.get())
        if memory_size != 0:
            if memory_size > MAX_MEMORY_SIZE:
                memory_size = MAX_MEMORY_SIZE
            elif memory_size < MIN_MEMORY_SIZE:
                memory_size = MIN_MEMORY_SIZE

        subprograms = 0 if not bool(self.subprograms_allowed_var.get()) else int(self.subprograms_count_var.get())
        if memory_size != 0:
            if memory_size > MAX_MEMORY_SIZE:
                memory_size = MAX_MEMORY_SIZE
            elif memory_size < MIN_MEMORY_SIZE:
                memory_size = MIN_MEMORY_SIZE

        disabled = []
        for command in self.banned_commands_text.get("1.0", tk.END).split(","):
            command = command.strip().upper()
            if len(command) != 0:
                disabled.append(command)

        new_level_data = {
            "info": {
                "title": self.title_text.get("1.0", tk.END).strip(),
                "description": self.description_text.get("1.0", tk.END).strip()
            },
            "mission": self.mission_text.get("1.0", tk.END).strip(),
            "grid_coords": bool(self.grid_coords_var.get()),
            "limitations": {
                "stack_size": stack_size,
                "memory_size": memory_size,
                "subprograms": subprograms,
                "disabled": disabled
            },
            "tests": [test.get() for test in self.tests]
        }

        if new_level_data == self.level_data:
            return False
        else:
            self.level_data = new_level_data
            return True

    def load_level_data(self):
        info = self.level_data.get("info", BASIC_LEVEL["info"])
        self.title_text.delete("1.0", tk.END)
        self.title_text.insert("1.0", info["title"])

        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", info["description"])

        self.mission_text.delete("1.0", tk.END)
        self.mission_text.insert("1.0", self.level_data.get("mission", ""))

        self.grid_coords_var.set(int(self.level_data.get("grid_coords", False)))

        limitations = self.level_data.get("limitations", BASIC_LEVEL["limitations"])
        stack_size = limitations["stack_size"]
        if stack_size == 0:
            self.stack_allowed_var.set(int(False))
            self.stack_size_var.set(str(1))
        else:
            if stack_size > MAX_STACK_SIZE:
                stack_size = MAX_STACK_SIZE
            elif stack_size < MIN_STACK_SIZE:
                stack_size = MIN_STACK_SIZE
            self.stack_allowed_var.set(int(True))
            self.stack_size_var.set(str(stack_size))

        memory_size = limitations["memory_size"]
        if memory_size == 0:
            self.memory_allowed_var.set(int(False))
            self.memory_size_var.set(str(1))
        else:
            if memory_size > MAX_MEMORY_SIZE:
                memory_size = MAX_MEMORY_SIZE
            elif memory_size < MIN_MEMORY_SIZE:
                memory_size = MIN_MEMORY_SIZE
            self.memory_allowed_var.set(int(True))
            self.memory_size_var.set(str(memory_size))

        subprograms = limitations["subprograms"]
        if memory_size == 0:
            self.subprograms_allowed_var.set(int(False))
            self.subprograms_count_var.set(str(1))
        else:
            if subprograms > MAX_SUBPROGRAMS:
                subprograms = MAX_SUBPROGRAMS
            elif subprograms < MIN_SUBPROGRAMS:
                subprograms = MIN_SUBPROGRAMS
            self.subprograms_allowed_var.set(int(True))
            self.subprograms_count_var.set(str(subprograms))

        disabled = copy(limitations["disabled"])   # Make it point to a copy instead of the "disabled" array in the dict, so we can use pop safely
        self.banned_commands_text.delete("1.0", tk.END)
        if len(disabled) != 0:
            self.banned_commands_text.insert("1.0", disabled.pop(0))
            for command in disabled:
                self.banned_commands_text.insert(tk.END, ", ")
                self.banned_commands_text.insert(tk.END, command)

        self.toggle_grid_coords()
        self.toggle_stack_allowed()
        self.toggle_memory_allowed()
        self.toggle_subprograms_allowed()

        self.tests = [AssemBlocksTest(test) for test in self.level_data.get("tests", BASIC_LEVEL["tests"])]
        self.tests_list.delete(0, tk.END)
        for i in range(len(self.tests)):
            self.tests_list.insert(tk.END, "Test {}".format(i+1))

        self.check_test_buttons()
        self.tests_list.activate(0)
        self.select_test()

    def toggle_grid_coords(self):
        if bool(self.grid_coords_var.get()):
            self.test_width_spinbox.configure(to=MAX_GRID_SIZE-1)
            self.test_height_spinbox.configure(to=MAX_GRID_SIZE-1)
        else:
            self.test_width_spinbox.configure(to=MAX_GRID_SIZE)
            self.test_height_spinbox.configure(to=MAX_GRID_SIZE)

        self.test_spawn_column_spinbox.configure(to=self.test_width_spinbox.cget("to"))
        self.test_spawn_row_spinbox.configure(to=self.test_height_spinbox.cget("to"))

    def toggle_stack_allowed(self):
        if bool(self.stack_allowed_var.get()):
            self.stack_size_spinbox.configure(state=tk.NORMAL)
        else:
            self.stack_size_spinbox.configure(state=tk.DISABLED)

    def toggle_memory_allowed(self):
        if bool(self.memory_allowed_var.get()):
            self.memory_size_spinbox.configure(state=tk.NORMAL)
        else:
            self.memory_size_spinbox.configure(state=tk.DISABLED)

    def toggle_subprograms_allowed(self):
        if bool(self.subprograms_allowed_var.get()):
            self.subprograms_count_spinbox.configure(state=tk.NORMAL)
        else:
            self.subprograms_count_spinbox.configure(state=tk.DISABLED)

    def add_test(self):
        self.tests_list.insert(tk.END, "Test {}".format(self.tests_list.size() + 1))
        self.tests.append(AssemBlocksTest(BASIC_TEST))

        self.check_test_buttons()

    def remove_test(self):
        self.tests_list.delete(tk.END)
        self.tests.pop()

        self.check_test_buttons()

    def check_test_buttons(self):
        amount = len(self.tests)
        self.add_test_button.configure(state=tk.NORMAL)
        self.delete_test_button.configure(state=tk.NORMAL)
        if amount == 1:
            self.delete_test_button.configure(state=tk.DISABLED)
        elif amount == MAX_TESTS:
            self.add_test_button.configure(state=tk.DISABLED)

    def select_test(self, *args):
        self.selected_test = self.tests[self.tests_list.index(tk.ACTIVE)]
        self.test_width_var.set(str(self.selected_test.width))
        self.test_height_var.set(str(self.selected_test.height))
        self.draw_test()

    def draw_test(self):
        self.selected_test.draw_start(self.tests_canvas_start)
        self.selected_test.draw_wanted(self.tests_canvas_wanted)

if __name__ == "__main__":
    tk.CallWrapper = Catcher

    root = tk.Tk()
    root.title("AssemBlocks level editor")
    root.resizable(False, False)

    for square_type in SQUARE_TYPES:
        images[square_type] = PNGImage(file=os.path.join(IMAGE_FOLDER, square_type + ".png"))
    images["robot"] = PNGImage(file=os.path.join(IMAGE_FOLDER, "robot.png"))

    app = Application(root)

    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
