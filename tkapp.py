# ==========================================================
# DICOM Toolbox
# Author: Marcin Leśniak, PhD
#
# TKapp
# ==========================================================
from tkinter.messagebox import showinfo
from tkinter import filedialog, PhotoImage
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
#from ttkbootstrap.style import Bootstyle
from ttkbootstrap import Messagebox
from constants import Constants, Caps, PLMessageDialog, PLWarning, PLQuerybox
from pathlib import Path
import shutil
import pydicom
import numpy as np
from PIL import Image, ImageTk
import json
#from functools import partial
from pprint import pprint
from helpers import resource_path
import logging
#import time

# Configure logging
logging.basicConfig(filename=resource_path('log/errors.log'),
                    level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s')

class App(ttk.Window):
    def __init__(self) -> None:
        super().__init__(title=Constants.APP_TITLE, themename=Constants.APP_THEME, size=Constants.WINDOW_SIZE, resizable=(1, 1))

        logo_path = resource_path(Constants.ASSETS_FOLDER+"icon.png")
        self._app_icon = PhotoImage(file=str(logo_path))
        self.wm_iconphoto(False, self._app_icon)

        self.folder_var = ttk.StringVar()
        self.target_folder_var = ttk.StringVar()
        self.info_folder = ttk.StringVar(value="status...")
        self.extension = ttk.StringVar(value="dcm")
        self.size = ttk.StringVar(value="512")
        self.info_selected_file = ttk.StringVar()
        self.progress = ttk.IntVar(value=0)
        self.folder = None
        self.original_image = None
        self.photo = None
        self.dicom_preview = ttk.BooleanVar()
        self.files_change = None
        self.info_error = ttk.StringVar()

        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.frame = ttk.Frame(master=self, padding=10)
        self.frame.grid(column=0, row=0, sticky=NSEW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        #self.rowconfigure(5, weight=1)
        #self.frame.pack(fill=BOTH, expand=YES)
        self.frame.style = ttk.Style()
        self.frame.style.configure('.', font=('Consolas', 11))

        menubar = ttk.Menu(self)
        file_menu = ttk.Menu(menubar, tearoff=False)
        #file_menu.add_command(label="New", command=lambda: print("new"))
        file_menu.add_command(label="Otwórz katalog źródłowy", command=self.select_folder)
        file_menu.add_command(label="Otwórz katalog docelowy", command=self._select_target_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Wyjdź", command=self.on_close)
        menubar.add_cascade(label="Plik", menu=file_menu)

        about_menu = ttk.Menu(menubar, tearoff=False)
        about_menu.add_command(label="O programie", command=self.show_info)
        menubar.add_cascade(label="Info", menu=about_menu)
        self.config(menu=menubar)

        self._create_widgets(master=self.frame)


    def _create_widgets(self, master) -> None:

        #====================== LEFT PANEL ====================
        self.button_entry_folder = ttk.Button(master, text="Katalog wejściowy", command=self.select_folder, bootstyle="secondary[300]", icon="folder")

        self.entry_path = ttk.Entry(master=master, textvariable=self.folder_var)
        self.entry_path.bind("<Return>", self.on_entry_path_enter)
        self.target_path = ttk.Entry(master=master, textvariable=self.target_folder_var)

        self.file_list = ttk.Treeview(master, columns=("filename", "size"), show="headings", height=5, bootstyle="info[200]")
        self.file_list.heading("filename", text="nazwa")
        self.file_list.heading("size", text="rozmiar")
        self.file_list.column("filename", anchor=W)
        self.file_list.column("size", anchor=W)
        self.file_list.bind("<<TreeviewSelect>>", self.select_file)

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(master, orient=VERTICAL, command=self.file_list.yview)

        self.file_list.configure(yscrollcommand=self.scrollbar.set)
        self.file_list.bind("<Control-a>", self.select_all)
        self.label_info_folder = ttk.Label(master, textvariable=self.info_folder)

        #button
        self.button_selectall = ttk.Button(master, text="Zaznacz wszystkie", command=self.select_all, bootstyle="secondary[300]", icon="check2-all")
        self.button_selectall.state(["disabled"])
        
        self.button_ext = ttk.Button(master, text="Dodaj rozszerzenie", command=self.add_extension, bootstyle="secondary[300]", icon="file-earmark-plus")
        self.button_ext.state(["disabled"]) 
        self.entry_ext = ttk.Entry(master=master, textvariable=self.extension)

        self.button_size = ttk.Button(master, text="Zmień rozdzielczość", command=self.change_size, bootstyle="secondary[300]", icon="arrows-angle-contract")
        self.button_size.state(["disabled"])
        self.entry_size = ttk.Entry(master=master, textvariable=self.size)

        self.progress_bar = ttk.Progressbar(master, variable=self.progress, maximum=100, bootstyle="success", mode="determinate")
        self.progress.set(0) 
        self.label_errors = ttk.Label(master, textvariable=self.info_error, font=('Arial', 8))

        #====================== RIGHT PANEL ====================

        self.button_target_folder = ttk.Button(master, text="Katalog docelowy", command=self._select_target_folder, bootstyle="secondary[300]", icon="folder")
        #self.label_selected_file = ttk.Label(master, textvariable=self.info_selected_file, justify="left", anchor="nw", foreground="#b02a37", background=self.style.colors.bg, width=50, font=('Arial', 8))
        self.text_selected_file = ttk.ScrolledText(master, width=40, height=10, wrap="word", auto_hide=True, foreground="#b02a37", background=self.style.colors.bg, font=('Arial', 8))
        #self.text_selected_file.configure(state="disabled")
        self.check_dicom_preview = ttk.Checkbutton(master, text="Włącz podgląd", variable=self.dicom_preview)
        self.check_dicom_preview.configure(takefocus=False)
        self.canvas = ttk.Canvas(master, width=50, height=250, autostyle=False, background=self.style.colors.bg, highlightthickness=0)

        #====================== LEFT PANEL GRID ====================
        self.button_entry_folder.grid(column=0, row=0, sticky=NSEW, padx=1, pady=2, columnspan=2)
        self.button_target_folder.grid(column=3, row=0, sticky=NSEW, padx=1, pady=2, columnspan=2)

        self.entry_path.grid(column=0, row=1, sticky=NSEW, padx=1, pady=2, columnspan=2)
        self.target_path.grid(column=3, row=1, sticky=NSEW, padx=1, pady=2, columnspan=2)
        self.file_list.grid(column=0, row=2, sticky=NSEW, padx=1, pady=2, columnspan=2)
        self.scrollbar.grid(column=2, row=2, sticky=NS, padx=1, pady=2, columnspan=1)
        self.label_info_folder.grid(column=0, row=3, sticky=NSEW, padx=1, pady=2, columnspan=1)
        self.button_selectall.grid(column=1, row=3, sticky=NSEW, padx=1, pady=20, columnspan=1)
        self.button_ext.grid(column=0, row=4, sticky=NSEW, padx=1, pady=20, columnspan=1)
        self.entry_ext.grid(column=1, row=4, sticky=NSEW, padx=1, pady=20, columnspan=1)
        self.button_size.grid(column=0, row=5, sticky=NSEW, padx=1, pady=20, columnspan=1)
        self.entry_size.grid(column=1, row=5, sticky=NSEW, padx=1, pady=20, columnspan=1)

        self.progress_bar.grid(column=0, row=6, sticky=EW, padx=1, pady=2, columnspan=5)
        self.label_errors.grid(column=0, row=7, sticky=EW, padx=1, pady=2, columnspan=5)

        #====================== RIGHT PANEL GRID ====================

        #self.label_selected_file.grid(column=3, row=2, sticky=NSEW, padx=1, pady=2, columnspan=2, rowspan=1)
        self.text_selected_file.grid(column=3, row=2, sticky=NSEW, padx=1, pady=2, columnspan=2, rowspan=1)

        self.check_dicom_preview.grid(column=3, row=3, sticky=NSEW, padx=1, pady=2, columnspan=1, rowspan=1)
        self.canvas.grid(column=4, row=3, sticky=NSEW, padx=1, pady=2, columnspan=1, rowspan=3)
        self.canvas.bind("<Configure>", self._reposition_image)

        # Allow the Treeview to expand
        master.columnconfigure(0, weight=1)
        master.columnconfigure(4, weight=1)
        master.rowconfigure(2, weight=1)


    def show_info(self):
        Messagebox.show_info(
            title="O programie", 
            message=f"Autor: {Constants.AUTHOR}\nWersja: {Constants.VERSION}\nProgram umożliwia zmianę rozdzielczości i rozszerzenia plików DICOM",
            icon=self._app_icon) 


    def select_folder(self) -> None:

        config_path = resource_path(Constants.SETTINGS_PATH)
        with open(config_path, 'r', encoding="utf-8") as f:
            settings = json.load(f)
        init_dir = settings['settings']['path']
         
        folder = filedialog.askdirectory(parent=self, title="Wybierz folder", initialdir=init_dir)

        if folder:
            self.folder_var.set(folder)
            self.folder = Path(folder)
            #print(self.folder_var.get(), " - ", type(self.folder_var.get()))
            settings['settings']['path'] = self.folder_var.get()
            #pprint(settings)
            with open(config_path, 'w', encoding="utf-8") as f:
               json.dump(settings, f)

            self._update_file_list()
        

    def select_file(self, event) -> None:

        selected = self.file_list.selection()

        if not selected:
            return

        iid = selected[0]
        item = self.file_list.item(iid)
        file_name = f"{self.folder_var.get()}/{item['values'][0]}"
        #self.info_error.set(f"selected: {Path(file_name).name}")
        #print(f"selected: {Path(file_name).name}")
        #print(self.dicom_preview.get())
        self.button_ext.state(["!disabled"])

        try: 
            ds = pydicom.dcmread(file_name)

            info_head = []
            info_full = []

            for name, tag in Constants.TAGS.items():
                info_head.append(f"{name}: {getattr(ds, name.replace(' ', ''), None)}")
            
            for elem in ds:
                value = elem.value

                if elem.tag == (0x7FE0, 0x0010):
                    continue  # Skip PixelData

                if value is None:
                    continue

                if isinstance(value, str) and not value.strip():
                    continue

                if isinstance(value, (list, tuple)) and len(value) == 0:
                    continue


                info_full.append(f"{elem.name}: {value}")
                
            pixels = self._open_dicom(ds)
            height, width  = pixels.shape
            info_head.insert(0, f"{'Resolution'}: {width}:{height}")

            #print(f"{Path(file_name).name}\n" + "\n".join(info))

            #self.info_selected_file.set(f"{Path(file_name).name}\n" + "\n".join(info))
            self.text_selected_file.delete("1.0", "end")
            self.text_selected_file.insert("1.0", 
                                           f"{Path(file_name).name}\n" + "\n".join(info_head) +
                                           f"\n\nPEŁNE METADANE:\n" + "\n".join(info_full))

            if self.dicom_preview.get():
                self._display_dicom(pixels)

            self.button_size.state(["!disabled"])
            if len(selected) > 1:
                self.selected_multiple()
            else:
                self.info_error.set("")

        except (pydicom.errors.InvalidDicomError) as e:
            #print("not a valid DICOM file")
            #self.info_selected_file.set("Plik DICOM niepoprawny")
            logging.error(f"Error in select_file: {e}")
            self.info_error.set(e)
            self.text_selected_file.delete("1.0", "end")
            self.text_selected_file.insert("1.0", "Plik DICOM niepoprawny")
            self.canvas.delete("all")
            self.button_size.state(["!disabled"])


    def select_all(self, event=None) -> str:
        self.file_list.selection_set(self.file_list.get_children())
        self.button_size.state(["!disabled"])
        self.button_ext.state(["!disabled"])
        self.selected_multiple()
        return "break"


    def selected_multiple(self) -> None:
        selected = list(self.file_list.selection())
        slices = []

        for iid in selected:
            item = self.file_list.item(iid)
            file_name = f"{self.folder_var.get()}/{item['values'][0]}"
            ds = ds = pydicom.dcmread(file_name, stop_before_pixels=True)
            ipp = np.array(ds.ImagePositionPatient, dtype=float)
            iop = np.array(ds.ImageOrientationPatient, dtype=float)
            slices.append((ipp, iop, file_name))
        
        if len(slices) < 2:
            raise ValueError("Need at least 2 valid DICOM slices.")

        # Use the first slice's orientation to get the slice normal
        iop = slices[0][1]
        row_direction = iop[:3]
        col_direction = iop[3:]

        normal = np.cross(row_direction, col_direction)
        normal /= np.linalg.norm(normal)

        # Project each 3D position onto the slice normal
        positions = [
            (np.dot(ipp, normal), ipp, file_name)
            for ipp, _, file_name in slices
        ]

        # Sort slices by their physical position
        positions.sort(key=lambda x: x[0])

        # Calculate distances between consecutive slices
        projections = np.array([p[0] for p in positions])
        spacings = np.diff(projections)

        m1 = f"Liczba warstw: {len(positions)} "
        m2 = f"Odstępy między warstwami (mm): {spacings}"
        m3 = f"Mediana odstępów między warstwami: {np.median(spacings):.2f} mm"
        #print(f"{m1} {m2} {m3}")
        self.info_error.set(m1 + m3)


    def on_entry_path_enter(self, event=None):
        #self.folder_var.set(folder)
        self.folder = Path(self.folder_var.get())
        self._update_file_list()


    def _update_file_list(self) -> None:
        # Remove previous files
        self.file_list.delete(*self.file_list.get_children())

        # Add files
        self.files = iter(self.folder.iterdir())
        self.num_files = sum(1 for _ in self.folder.iterdir())
        #step = 100//num_files
        self.processed_files = 0
        self.progress.set(0)

        if self.num_files == 0:
            return

        #self._update_next_file()

        for file in self.files:
            if file.is_file():
                size = file.stat().st_size // 1024
            
                self.file_list.insert(
                    "",
                    END,
                    values=(file.name, f"{size:,d}KB")
                )


        self.button_selectall.state(["!disabled"])
        self.info_folder.set(f"Plików w folderze: {self.num_files}")
        self.text_selected_file.delete("1.0", "end")


    # def _update_next_file(self) -> None:
    #     try:
    #         file = next(self.files)
    #     except StopIteration:
    #         self.progress.set(100)
    #         return

    #     if file.is_file():
    #         size = file.stat().st_size

    #         self.file_list.insert(
    #             "",
    #             END,
    #             values=(file.name, size)
    #         )

    #     self.processed_files += 1
    #     self.progress.set(
    #         self.processed_files / self.num_files * 100
    #     )

    #     # Process the next file after Tkinter has had a chance
    #     # to update the interface.
    #     self.after(10, self._update_next_file)


    # ============== DICOM EXTENSION ==================

    def add_extension(self) -> None:
        target = self.target_folder_var.get().strip()
        target_folder = Path(target)
        #source = self.folder_var.get().strip()

        if not target:
            dialog = PLWarning(
                message=f"Wybierz katalog docelowy",
                title="Uwaga!",
                parent=self,
            )
    
            dialog.show()
            return

        def handle_answer():
            answer = dialog.result
            
            if answer == Caps.CAP_YES:
                self._change_extensions(target_folder)

            elif answer == Caps.CAP_NO:
                #print("No changes")
                self.info_error.set("No changes")

        dialog = PLMessageDialog(
            message=f"Zmienić rozszerzenia plików?\nZaznaczonych plików: {len(self.file_list.selection())}",
            title="Potwierdzenie zmian",
            command=handle_answer,
            parent=self,
        )

        dialog.show()
 

    def _change_extensions(self, target_folder: Path) -> None:
        self.source_directory = Path(self.folder_var.get())
        self.target_folder = target_folder
        #self.extension.set(self.entry_ext.get().strip().lstrip("."))
        self.selected_items = list(self.file_list.selection())
        self.num_files = len(self.selected_items)
        self.file_index = 0
        self.counter = 0
        self.change_all = False

        self.progress.set(0)

        if self.num_files == 0:
            return

        self._process_next_extension()


    def _process_next_extension(self) -> None:
        # All selected files have been processed
        if self.file_index >= self.num_files:
            self.progress.set(100)
            #self._update_file_list()

            #print(f"Extension added to: {self.counter} files")
            self.info_error.set(f"Rozszerzenie dodane do {self.file_index} {'pliku' if self.file_index == 1 else 'plików'}")
            return

        item_id = self.selected_items[self.file_index]
        values = self.file_list.item(item_id, "values")

        if values:
            source_path = self.source_directory / values[0]

            if source_path.is_file():
                target_path = self.target_folder / (
                    source_path.with_suffix(f".{self.extension.get().strip()}").name
                )

                res = self._save_file(
                    source_path=source_path,
                    target_path=target_path,
                    change_all=self.change_all
                )

                #print("res:", res)

                if res:
                    self.counter += 1
                    self.change_all = (res == 2)

        # Advance the progress, including skipped files
        self.file_index += 1
        self.progress.set(
            self.file_index / self.num_files * 100
        )

        # Schedule the next file
        self.after(10, self._process_next_extension)


    def change_size(self) -> None:
        source = self.folder_var.get().strip()
        target = self.target_folder_var.get().strip()

        if (not source) or (not target):
            dialog = PLWarning(
                message=f"Wybierz katalog docelowy",
                title="Uwaga!",
                parent=self,
            )
    
            dialog.show()
            return
        else:
            source_directory = Path(source)
            target_folder = Path(target)
        
        def handle_answer():
            answer = dialog.result
            
            if answer == Caps.CAP_YES:
                self._resize_dicom(source_directory, target_folder)

            elif answer == Caps.CAP_NO:
                #print("No changes")
                self.info_error.set("No changes")

        dialog = PLMessageDialog(
            message=f"Zmienić rozmiar obrazów?\nZaznaczonych plików: {len(self.file_list.selection())}",
            title="Potwierdzenie zmian",
            command=handle_answer,
            parent=self,
        )
        
        dialog.show()
        

    # ============== DICOM RESIZE ==================

    def _resize_dicom(self, source_directory: Path, target_folder: Path, size=(512, 512)) -> None:

        self.files_change = None

        try:
            x = int(self.size.get().strip())
            size = (x, x)
        except ValueError as e:
            #print(e)
            logging.error(f"Error in _resize_dicom: {e}")
            self.info_error.set(e)
            return

        self.resize_source_directory = source_directory
        self.resize_target_folder = target_folder
        self.resize_size = size

        self.resize_items = list(self.file_list.selection())
        self.resize_num_files = len(self.resize_items)
        self.resize_index = 0
        self.resize_counter = 0
        self.resize_change_all = False

        self.progress.set(0)

        if self.resize_num_files == 0:
            return

        self._resize_next_file()


    def _resize_next_file(self) -> None:

        # All selected files have been processed
        if self.resize_index >= self.resize_num_files:
            self.progress.set(100)

            nl = "\n"
            m1 = (
                f"Zmieniono rozdzielczość {self.resize_index} "
                f"{'pliku' if self.resize_index == 1 else 'plików'} "
                f"DICOM"
                f"{' i zapisano w: ' + str(self.resize_target_folder.as_posix()) if self.resize_index > 0 else '.'}"
            )

            #print(m1)
            self.info_error.set(m1)

            dialog = PLWarning(
                message=m1,
                title="Uwaga!",
                parent=self,
            )
            dialog.show()

            return

        item_id = self.resize_items[self.resize_index]
        values = self.file_list.item(item_id, "values")

        if values:
            source_path = self.resize_source_directory / values[0]

            if source_path.is_file():
                try:
                    # Read DICOM
                    ds = pydicom.dcmread(source_path)

                    # Get pixel data
                    image_array = ds.pixel_array

                    # Convert NumPy array -> Pillow image
                    image = Image.fromarray(image_array)

                    # Skip images smaller than the requested size
                    if image.size[0] >= self.resize_size[0]:

                        # Resize
                        resized = image.resize(
                            self.resize_size,
                            Image.Resampling.LANCZOS
                        )

                        # Convert Pillow image -> NumPy array
                        resized_array = np.asarray(resized)

                        # Update DICOM
                        ds.Rows = self.resize_size[1]
                        ds.Columns = self.resize_size[0]
                        ds.PixelData = resized_array.tobytes()

                        # Save to target folder
                        target_path = self.resize_target_folder / (
                            f"{source_path.stem}_"
                            f"{self.resize_size[0]}x"
                            f"{self.resize_size[1]}.dcm"
                        )

                        res = self._save_file(
                            target_path=target_path,
                            ds=ds,
                            change_all=self.resize_change_all
                        )

                        #print("res:", res)

                        if res:
                            self.resize_counter += 1
                            self.resize_change_all = (res == 2)

                except Exception as e:
                    # print(
                    #     f"Error processing {source_path.name}: {e}"
                    # )
                    logging.error(f"Error in _resize_next_file: {e}")
                    self.info_error.set(f"Error processing {source_path.name}: {e}")

        # Advance progress, even if the file was skipped or failed
        self.resize_index += 1

        self.progress.set(
            self.resize_index / self.resize_num_files * 100
        )

        # Schedule the next file
        self.after(10, self._resize_next_file)


    def _save_file(self, source_path: Path=None, target_path: Path=None, ds: pydicom.dataset.FileDataset=None, change_all: bool=None) -> int:
        '''
        Parameters:
            source_path: folder from which files will be copied
            target_path: folder to which files will be copied
            ds: pydicom dataset (dicom file)
            change_all: whether or not 'yes to all' option was selected
        Returns:
            0: do not overwrite
            1: overwrite one
            2: overwrite all
        '''
        #self.files_change = 3
        #print("change_all:", change_all)

        def handle_answer():
            answer = dialog.result

            if answer == Caps.CAP_NO:
                #print("No changes")
                self.info_error.set("No changes")
                self.files_change = 0
        
            elif answer == Caps.CAP_YES:
                #print("OK, można nadpisać")
                self.info_error.set("OK, można nadpisać")
                # #image.save(output_path)
                self.files_change = 1

            elif answer == Caps.CAP_YES_ALL:
                self.info_error.set("OK, można nadpisać wszystkie")
                #print("OK, można nadpisać wszystkie")
                #shutil.copy2(source_path, target_path)
                self.files_change = 2

        if target_path.exists() and not change_all:
            
            dialog = PLMessageDialog(
                message=f"Plik o nazwie {target_path.name} już istnieje w docelowym katalogu.\nNadpisać?",
                title="Plik istnieje!",
                command=handle_answer,
                buttons=[Caps.CAP_CANCEL, Caps.CAP_NO, Caps.CAP_YES, Caps.CAP_YES_ALL],
                parent=self,
            )
    
            dialog.show()

        if ds:
            ds.save_as(target_path)
        else:
            shutil.copy2(source_path, target_path)

        return self.files_change

        
    # ============== DICOM OPEN ==================

    def _open_dicom(self, ds: None) -> np.ndarray|None:

        if not ds:
            return None

        try:
            pixels = ds.pixel_array.astype(np.float32)
            #print(pixels.shape)

            # Apply Rescale Slope / Intercept when present
            slope = float(getattr(ds, "RescaleSlope", 1))
            intercept = float(getattr(ds, "RescaleIntercept", 0))
            pixels = pixels * slope + intercept

            # Normalize to 0-255
            pixels -= pixels.min()

            if pixels.max() > 0:
                pixels = pixels / pixels.max() * 255

            pixels = pixels.astype(np.uint8)

            return pixels

        except (pydicom.errors.InvalidDicomError, Exception) as e:
            #print("problem with a DICOM file")
            logging.error(f"Error in _open_dicom: {e}")
            self.info_error.set(e)
            return None


    # ============== DICOM DISPLAY ==================

    def _display_dicom(self, pixels: np.ndarray) -> None:
        self.original_image = Image.fromarray(pixels)
        self._reposition_image()


    def _reposition_image(self, event=None) -> None:
        # if not hasattr(self, "photo"):
        #     return
        if self.original_image is None:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        image_width, image_height = self.original_image.size

        x = (canvas_width - image_width) // 2
        y = (canvas_height - image_height) // 2

         # Scale image so it fits completely inside the canvas.
        scale = min(
            canvas_width / image_width,
            canvas_height / image_height
        )

        new_width = max(1, int(image_width * scale))
        new_height = max(1, int(image_height * scale))

        resized = self.original_image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

        self.photo = ImageTk.PhotoImage(resized)

        self.canvas.delete("dicom_image")

        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2

        self.canvas.create_image(
            x,
            y,
            anchor="nw",
            image=self.photo,
            tags="dicom_image"
        )

        #self.canvas.coords("dicom_image", x, y)


    def _select_target_folder(self) -> None:

        config_path = resource_path(Constants.SETTINGS_PATH)
        with open(config_path, 'r', encoding="utf-8") as f:
            settings = json.load(f)
        init_dir = settings['settings']['target']
        
        folder = filedialog.askdirectory(parent=self, title="Wybierz folder", initialdir=init_dir)

        
        if folder:
            folder = Path(folder)
            name = PLQuerybox.get_string(
                prompt="Jeśli chcesz stworzyć nowy folder, podaj jego nazwę.\nJeśli nie, pozostaw okno edycji puste.",
                title="Nowy folder?",
                parent=self,
            )
            if name is None:
                return
            
            if name.strip():
                folder = folder / name
                folder.mkdir(parents=True, exist_ok=True)

            self.target_folder_var.set(str(folder.as_posix()))
            settings['settings']['target'] = self.target_folder_var.get()
            #pprint(settings)
            with open(config_path, 'w', encoding="utf-8") as f:
               json.dump(settings, f)


    # ============== CLOSE ====================

    def on_close(self) -> None:
        '''
        Called when close icon clicked
        Safely kill the app
        '''

        self.quit()
        self.destroy()
        
        print(f"App closed")
