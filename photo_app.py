import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
import os 
import shutil 
import random
from PIL import Image, ImageTk 

# ===============================================
# BAGIAN 1: DEFINISI CLASS FOTO (OBJECT)
# (Tidak Ada Perubahan)
# ===============================================

class Foto:
    """Blueprint for a Photo object (Model Data)."""
    def __init__(self, nama_file, path_lengkap, rating=0, tags=[]):
        self.nama_file = nama_file
        self.path_lengkap = path_lengkap 
        self.rating = rating
        self.tags = list(tags)

    def beri_rating(self, nilai):
        """Method to change the rating with validation."""
        if 1 <= nilai <= 5:
            self.rating = nilai
            return True
        return False

    def tambah_tag(self, tag_baru):
        """Method to add a tag to the photo."""
        # Clean up and capitalize tag
        tag_baru = tag_baru.strip().capitalize()
        if tag_baru and tag_baru not in self.tags:
            self.tags.append(tag_baru)
            self.tags.sort() 
            return True
        return False
    
    def hapus_tag(self, tag_yang_dihapus):
        """Method to remove a tag from the photo."""
        # Tag deletion must be case-sensitive to match saved tag
        if tag_yang_dihapus in self.tags:
            self.tags.remove(tag_yang_dihapus)
            return True
        return False

    def get_info(self):
        """Returns basic information string (Tags are displayed separately)."""
        return (f"File: {self.nama_file}\n"
                f"Rating: {self.rating} / 5\n")
    
# ===============================================
# BAGIAN 2: DEFINISI CLASS PHOTOAPP (GUI APPLICATION & COLLECTION LOGIC)
# ===============================================

class PhotoApp:
    def __init__(self, master):
        self.master = master
        master.title("Photo Rating & Tagging System (Klasifikasi Foto)")
        master.geometry("1200x800") 

        # State Variables
        self.koleksi_foto = []
        self.index_foto_saat_ini = 0
        self.foto_tk = None # Tkinter PhotoImage reference
        
        # Tag Management Variables
        self.kriteria_tag_list = set() # Tags added by user for quick tagging buttons
        self.tag_unik_koleksi = set()  # Unique tags existing in ALL photos (for Photo Group Dropdown)
        self.kelompok_tag_var = tk.StringVar(self.master)
        
        # Setup GUI
        self.buat_layar_utama()
        self.buat_beranda()
        
        # Initial Screen
        self.tampilkan_layar(self.frame_beranda)
        
        # Setup Keyboard Shortcuts
        self.binding_keyboard()


    # --- Keyboard Binding Method (Shortcut) ---
    def binding_keyboard(self):
        """Sets keyboard shortcuts: Shift+1 to Shift+5 for rating, Left/Right Arrow for navigation."""
        # Rating Binding: Shift + 1 through 5
        for i in range(1, 6):
            # Penting: Menggunakan lambda event, val=i: untuk mengatasi masalah scoping loop
            self.master.bind(f"<Shift-KeyPress-{i}>", lambda event, val=i: self.aksi_simpan_rating_shortcut(val))

        # Navigation Binding: Left/Right Arrow
        self.master.bind("<Right>", lambda event: self.selanjutnya())
        self.master.bind("<Left>", lambda event: self.sebelumnya())


    # --- Screen Transition Method ---
    def tampilkan_layar(self, frame_yang_ditampilkan):
        """Hides all frames and displays the requested frame."""
        for frame in [self.frame_beranda, self.frame_utama]:
            frame.pack_forget()
        
        frame_yang_ditampilkan.pack(fill=tk.BOTH, expand=True)

    # --- Home Screen ---
    def buat_beranda(self):
        self.frame_beranda = ttk.Frame(self.master, padding="50")
        
        ttk.Label(self.frame_beranda, text="SELAMAT DATANG DI PHOTO MANAGER", 
                  font=('Montserrat', 18, 'bold')).pack(pady=20)
        
        ttk.Label(self.frame_beranda, text="Silakan impor folder foto untuk memulai klasifikasi.", 
                  font=('Montserrat', 12)).pack(pady=10)
        
        ttk.Button(self.frame_beranda, 
                   text="🚀 IMPOR FOLDER FOTO", 
                   command=self.aksi_import_folder,
                   style='Accent.TButton' 
                   ).pack(pady=30, ipadx=20, ipady=10)
        
    # --- Function/Method to Create Main Screen GUI Elements (3 Columns) ---
    def buat_layar_utama(self):
        self.frame_utama = ttk.Frame(self.master)
        
        # 1. Control Frame (Left)
        self.frame_kontrol = ttk.Frame(self.frame_utama, padding="10", width=250)
        self.frame_kontrol.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.frame_kontrol.pack_propagate(False) # Fixed width for Control Frame
        
        # Button to return to Home
        ttk.Button(self.frame_kontrol, 
                   text="← Kembali ke Import", 
                   command=lambda: self.tampilkan_layar(self.frame_beranda)
                   ).pack(fill=tk.X, pady=(0, 20))
        
        # --- PHOTO CONTROL ---
        ttk.Label(self.frame_kontrol, text="PHOTO CONTROL", font=('Montserrat', 12, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # A. Rating
        ttk.Label(self.frame_kontrol, text="Beri Rating (Shift + 1-5):").pack(anchor='w', pady=5)
        self.frame_rating_tombol = ttk.Frame(self.frame_kontrol)
        self.frame_rating_tombol.pack(fill=tk.X, pady=5)
        
        for i in range(1, 6):
            ttk.Button(self.frame_rating_tombol, 
                       text=str(i), 
                       width=3,
                       command=lambda val=i: self.aksi_simpan_rating_tombol(val)
                       ).pack(side=tk.LEFT, padx=3, pady=2)
                        
        # B. Add Tag Criteria
        ttk.Label(self.frame_kontrol, text="Tambah Tag Kriteria :", font=('Montserrat', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        self.tag_entry = ttk.Entry(self.frame_kontrol)
        self.tag_entry.pack(fill=tk.X, pady=2)
        # Bind the Enter key to the entry widget itself for adding criteria
        self.tag_entry.bind("<Return>", lambda event: self.aksi_tambah_kriteria_tag())
        
        # C. Container to display added tag criteria (as buttons)
        ttk.Label(self.frame_kontrol, text="Tag Kriteria yang Tersedia:", font=('Montserrat', 10)).pack(anchor='w', pady=(10, 5))
        self.frame_tag_kriteria_list = ttk.Frame(self.frame_kontrol, padding=5, relief="groove", borderwidth=2)
        self.frame_tag_kriteria_list.pack(fill=tk.X, pady=5)
        
        # D. Navigation
        ttk.Separator(self.frame_kontrol, orient='horizontal').pack(fill=tk.X, pady=10)
        
        self.frame_navigasi = ttk.Frame(self.frame_kontrol)
        self.frame_navigasi.pack(fill=tk.X, pady=5)
        # Use large buttons for navigation
        ttk.Button(self.frame_navigasi, text="<", command=self.sebelumnya, style='Big.TButton', width=5).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(self.frame_navigasi, text=">", command=self.selanjutnya, style='Big.TButton', width=5).pack(side=tk.LEFT, expand=True, padx=5)


        # 2. Preview Frame (Center)
        self.frame_tengah = ttk.Frame(self.frame_utama, padding="10")
        # PERBAIKAN: Menggunakan expand=True agar frame tengah mengisi sisa ruang
        self.frame_tengah.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) 

        ttk.Label(self.frame_tengah, text="PHOTO REVIEW", font=('Montserrat', 14, 'bold')).pack(pady=5)
        
        # FRAME GAMBAR FIXED SIZE - TIDAK PERLU FIXED SIZE KARENA AKAN MENYESUAIKAN DENGAN FRAME_TENGAH YANG EXPAND
        # Hapus image_frame dan gunakan frame_tengah sebagai parent langsung
        
        # Label to display the image
        # PERBAIKAN: Ganti place() yang bermasalah dengan pack() atau grid()
        self.image_label = ttk.Label(self.frame_tengah, background="#eeeeee", text="Image Preview Placeholder", relief="sunken")
        # Gunakan pack dengan expand=True agar label gambar mengisi frame tengah.
        self.image_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True) 


        # 3. Info Frame (Right)
        self.frame_info_kanan = ttk.Frame(self.frame_utama, padding="10", width=250) # Ubah width agar sama
        self.frame_info_kanan.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.frame_info_kanan.pack_propagate(False) # Fixed width for Info Frame

        # --- METADATA INFO ---
        ttk.Label(self.frame_info_kanan, text="METADATA INFO", font=('Montserrat', 12, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.label_filename = ttk.Label(self.frame_info_kanan, text="File Name: -", wraplength=230)
        self.label_filename.pack(anchor='w', pady=1)

        self.label_rating = ttk.Label(self.frame_info_kanan, text="Rating: -")
        self.label_rating.pack(anchor='w', pady=1)

        ttk.Label(self.frame_info_kanan, text="Tags Applied:").pack(anchor='w', pady=(5, 1))

        # Frame to hold the tag buttons already applied to the photo
        self.frame_tag_metadata = ttk.Frame(self.frame_info_kanan)
        self.frame_tag_metadata.pack(fill=tk.X, pady=5)
        
        # --- PHOTO GROUP ---
        ttk.Separator(self.frame_info_kanan, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(self.frame_info_kanan, text="PHOTO GROUP", font=('Montserrat', 12, 'bold')).pack(anchor='w', pady=(0, 5))
        
        # Tag Criteria Dropdown
        self.kelompok_tag_var.set("Pilih Tag") 
        # Inisialisasi OptionMenu harus dengan tuple atau list yang benar
        self.kelompok_tag_dropdown = ttk.OptionMenu(
            self.frame_info_kanan, 
            self.kelompok_tag_var, 
            "Pilih Tag", # Nilai default
            "Pilih Tag"  # Pilihan awal (akan di-overwrite oleh update_dropdown)
        )
        self.kelompok_tag_dropdown.pack(fill=tk.X, pady=2)
        
        ttk.Button(self.frame_info_kanan, 
                   text="EXPORT A COPY", 
                   style='Accent.TButton',
                   command=self.aksi_tombol_kelompokkan).pack(fill=tk.X, pady=10)

    # ===============================================
    # METHOD PEMELIHARAAN TAG UNIK GLOBAL
    # ===============================================

    def recalculate_unique_collection_tags(self):
        """Regenerates the set of all unique tags present across ALL photos in the collection."""
        new_unique_tags = set()
        for foto in self.koleksi_foto:
            for tag in foto.tags:
                new_unique_tags.add(tag)
        self.tag_unik_koleksi = new_unique_tags
        
    # --- File and Import Logic Method ---
    def aksi_import_folder(self):
        """Opens folder dialog and loads photos into the collection."""
        folder_path = filedialog.askdirectory(title="Pilih Folder Foto")
        if not folder_path:
            return

        self.koleksi_foto = [] 
        self.tag_unik_koleksi = set() 
        self.kriteria_tag_list = set() 
        
        foto_ditemukan = 0
        tipe_foto = ('.jpg', '.jpeg', '.png', '.gif', '.tif')

        # Import Logic
        try:
            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith(tipe_foto):
                    full_path = os.path.join(folder_path, file_name)
                    
                    foto = Foto(file_name, full_path)
                    self.koleksi_foto.append(foto)
                    
                    # Update tag collection list based on initial state (should be empty here)
                    for tag in foto.tags:
                        self.tag_unik_koleksi.add(tag)
                    
                    foto_ditemukan += 1

        except Exception as e:
             messagebox.showerror("Import Error", f"Terjadi kesalahan saat membaca folder: {e}")
             return

        if foto_ditemukan > 0:
            self.tampilkan_layar(self.frame_utama)
            self.index_foto_saat_ini = 0
            self.update_tag_kriteria_view() 
            self.update_dropdown_photo_group()
            self.tampilkan_foto_saat_ini()
            messagebox.showinfo("Import Success", f"🎉 {foto_ditemukan} foto berhasil diimpor.")
        else:
            messagebox.showwarning("Warning", "Tidak ada file foto (JPG/PNG/GIF/TIF) yang ditemukan.")
            self.tampilkan_layar(self.frame_beranda) 

    # --- Tag Criteria Method (Left Control Panel) ---
    def aksi_tambah_kriteria_tag(self):
        """Adds a tag from the input to the criteria list, NOT to the photo."""
        tag_baru = self.tag_entry.get().strip().capitalize()
        
        if not tag_baru:
            messagebox.showwarning("Warning", "Nama Tag Kriteria tidak boleh kosong.")
            return

        if tag_baru not in self.kriteria_tag_list:
            self.kriteria_tag_list.add(tag_baru)
            self.update_tag_kriteria_view() # Update criteria button display
            self.tag_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", f"Tag Kriteria '{tag_baru}' sudah ada.")

    def aksi_hapus_kriteria_tag(self, tag_kriteria):
        """
        [PERBAIKAN UTAMA] 
        Adds a confirmation dialog (OK/Cancel) before deleting the criteria.
        Removes a tag from the available criteria list AND removes it from ALL photos, 
        then updates the UI globally.
        """
        
        # 1. ADD CONFIRMATION DIALOG 
        # Cek apakah user yakin untuk menghapus (askokcancel mengembalikan True jika OK)
        konfirmasi = messagebox.askokcancel(
            "Konfirmasi Penghapusan", 
            f"Anda yakin ingin menghapus tag kriteria '{tag_kriteria}'? Tindakan ini akan menghapus tag ini dari daftar kriteria DAN SEMUA FOTO dalam koleksi."
        )

        if not konfirmasi:
            return # Stop execution if user presses 'Cancel'
            
        # 2. Remove from Criteria List
        self.kriteria_tag_list.discard(tag_kriteria)
        self.update_tag_kriteria_view()
        
        # 3. Cascade Deletion from ALL Photos
        is_current_photo_affected = False
        
        for i, foto in enumerate(self.koleksi_foto):
            if foto.hapus_tag(tag_kriteria):
                # Check if the currently displayed photo was affected
                if i == self.index_foto_saat_ini:
                    is_current_photo_affected = True
                    
        # 4. Update Global Tag Collection and Dropdown (Photo Group)
        # Since the tag was globally deleted, remove it from the unique collection set
        self.tag_unik_koleksi.discard(tag_kriteria)
        self.update_dropdown_photo_group()

        # 5. Refresh current photo display if affected
        if is_current_photo_affected:
            self.tampilkan_foto_saat_ini()
            
        messagebox.showinfo("Kriteria Dihapus", 
                            f"Tag Kriteria '{tag_kriteria}' berhasil dihapus dari daftar DAN SEMUA FOTO.")


    def update_tag_kriteria_view(self):
        """Recreates the tag criteria buttons in Photo Control."""
        # Clear the criteria frame
        for widget in self.frame_tag_kriteria_list.winfo_children():
            widget.destroy()
            
        if not self.kriteria_tag_list:
            ttk.Label(self.frame_tag_kriteria_list, text="Tambahkan tag di atas.").pack(anchor='w', padx=5, pady=5)
            return
            
        # Display Tag Criteria as buttons with an X button
        sorted_kriteria = sorted(list(self.kriteria_tag_list))
        
        for tag in sorted_kriteria:
            # Container for the tag button and X button
            frame_tag = ttk.Frame(self.frame_tag_kriteria_list, relief="solid")
            frame_tag.pack(fill=tk.X, pady=2, padx=2)
            
            # Tag Button (to apply tag to the photo)
            ttk.Button(frame_tag, 
                       text=tag, 
                       style='Tag.TButton', # Custom style for tag button
                       command=lambda t=tag: self.aksi_terapkan_tag(t)
                       ).pack(side=tk.LEFT, fill=tk.X, expand=True)
                        
            # Delete Criteria Button (X)
            ttk.Button(frame_tag, 
                       text="X", 
                       width=3, 
                       style='Danger.TButton',
                       command=lambda t=tag: self.aksi_hapus_kriteria_tag(t)
                       ).pack(side=tk.RIGHT)
                        
    def aksi_terapkan_tag(self, tag_yang_diterapkan):
        """Applies a tag from the criteria to the current photo."""
        if not self.koleksi_foto: return

        foto_saat_ini = self.koleksi_foto[self.index_foto_saat_ini]
        
        if foto_saat_ini.tambah_tag(tag_yang_diterapkan):
            # Add to the unique tag collection list and update dropdown
            self.tag_unik_koleksi.add(tag_yang_diterapkan)
            self.update_dropdown_photo_group()
            self.tampilkan_foto_saat_ini() 
        else:
            messagebox.showwarning("Warning", f"Tag '{tag_yang_diterapkan}' sudah ada di foto ini.")
            
    # --- Grouping Logic Method ---
    def update_dropdown_photo_group(self):
        """Updates the option list in the Photo Group Dropdown based on the unique tag collection."""
        tag_list = sorted(list(self.tag_unik_koleksi))
        
        options = ["Pilih Tag"] + tag_list        
        # Reset OptionMenu menu
        menu = self.kelompok_tag_dropdown["menu"]
        menu.delete(0, "end")
        
        for tag in options:            
            menu.add_command(label=tag, command=tk._setit(self.kelompok_tag_var, tag))

        # Reset selection if the currently selected tag was just removed
        current_selection = self.kelompok_tag_var.get()
        if current_selection not in options:
            self.kelompok_tag_var.set("Pilih Tag")
        # Tambahkan pembaruan jika dropdown sedang menggunakan nilai default
        elif current_selection == "Pilih Tag" and len(options) > 1:            
            pass


    def aksi_tombol_kelompokkan(self):
        kriteria = self.kelompok_tag_var.get().strip()
        if kriteria == "Pilih Tag":
             messagebox.showwarning("Warning", "Pilih tag yang valid dari dropdown.")
             return
        self.aksi_pindahkan_file(kriteria)

    # ===============================================
    # PERUBAHAN UTAMA: MEMILIH LOKASI EKSPOR
    # ===============================================
    def aksi_pindahkan_file(self, kriteria_tag):
        """
        [PERUBAHAN UTAMA]
        Menyalin file dengan kriteria tag ke folder baru yang dipilih pengguna.
        """
        # Ensure tag is not the placeholder
        if kriteria_tag == "Pilih Tag":
            return

        # 1. TAMPILKAN DIALOG UNTUK MEMILIH FOLDER UTAMA
        lokasi_dasar = filedialog.askdirectory(title=f"Pilih Folder Tujuan untuk Tag: {kriteria_tag}")
        
        if not lokasi_dasar:
            # Pengguna membatalkan dialog
            messagebox.showwarning("Dibatalkan", "Operasi penyalinan dibatalkan oleh pengguna.")
            return

        # 2. BUAT SUBFOLDER KHUSUS BERDASARKAN TAG DI DALAM FOLDER YANG DIPILIH
        # Bersihkan nama tag untuk digunakan sebagai nama folder
        safe_tag = "".join(c for c in kriteria_tag if c.isalnum() or c in (' ', '_')).rstrip()
        nama_folder_tag = f"KOLEKSI_{safe_tag.upper().replace(' ', '_')}"
        folder_output = os.path.join(lokasi_dasar, nama_folder_tag)
        
        if not os.path.exists(folder_output):
            try:
                os.makedirs(folder_output)
            except Exception as e:
                messagebox.showerror("Folder Error", f"Gagal membuat folder di lokasi yang dipilih: {e}")
                return
            
        foto_disalin = 0
        tag_kapital = kriteria_tag.strip().capitalize()
        
        # 3. LOGIKA PENYALINAN FILE
        for foto in self.koleksi_foto: 
            if tag_kapital in foto.tags:
                try:
                    tujuan_path = os.path.join(folder_output, foto.nama_file)
                    shutil.copy2(foto.path_lengkap, tujuan_path) # copy2 preserves metadata
                    foto_disalin += 1
                except Exception as e:
                    print(f"Failed to copy {foto.nama_file}: {e}")
                    
        if foto_disalin > 0:
            messagebox.showinfo("Grouping Complete", 
                                f"✅ {foto_disalin} foto dengan tag '{kriteria_tag}' berhasil dikelompokkan (disalin) ke:\n{folder_output}")
        else:
            messagebox.showwarning("Not Found", f"Tidak ada foto dengan tag '{kriteria_tag}' yang ditemukan.")

    # --- Navigation & Display Control Method ---    
    def tampilkan_foto_saat_ini(self):
        """Loads the image, resizes it, and displays the info."""
        if not self.koleksi_foto:            
            return

        foto_saat_ini = self.koleksi_foto[self.index_foto_saat_ini]
        
        # --- A. Display Metadata (Text Info) ---
        self.label_filename.config(text=f"File Name: {foto_saat_ini.nama_file}")
        self.label_rating.config(text=f"Rating: {foto_saat_ini.rating} / 5")
             
        self.perbarui_tampilan_tag_metadata(foto_saat_ini)


        # --- B. Display Image (Pillow Logic) ---
        try:
            img_pil = Image.open(foto_saat_ini.path_lengkap)
                        
            self.frame_tengah.update_idletasks()             
            max_width = self.image_label.winfo_width() 
            max_height = self.image_label.winfo_height() 
                       
            if max_width < 100 or max_height < 100:
                 max_width = 700 
                 max_height = 600

            lebar_asli, tinggi_asli = img_pil.size
            rasio_lebar = max_width / lebar_asli
            rasio_tinggi = max_height / tinggi_asli
            rasio = min(rasio_lebar, rasio_tinggi)
            
            # Ensure the image is not scaled up unnecessarily
            if rasio > 1:
                rasio = 1

            lebar_baru = int(lebar_asli * rasio)
            tinggi_baru = int(tinggi_asli * rasio)
            
            # Resize the image using Image.LANCZOS for high quality
            img_pil = img_pil.resize((lebar_baru, tinggi_baru), Image.LANCZOS)
            
            self.foto_tk = ImageTk.PhotoImage(img_pil)
            self.image_label.config(image=self.foto_tk, text="")
            
        except Exception as e:
            self.image_label.config(image='', text=f"Gagal memuat gambar: {e}", background="#ffdddd")
            
    def perbarui_tampilan_tag_metadata(self, foto):
        """Removes and recreates the applied Tag display in Metadata Info (Right Panel)."""
        
        # Clear frame
        for widget in self.frame_tag_metadata.winfo_children():
            widget.destroy()
            
        # If no tags, exit
        if not foto.tags:
            ttk.Label(self.frame_tag_metadata, text="- Belum ada tag -").pack(anchor='w', padx=5)
            return

        # Display Tag in Metadata Info (with delete button 'X')
        for tag in foto.tags:
            # Container for the tag text and X button
            frame_tag = ttk.Frame(self.frame_tag_metadata, borderwidth=1, relief="solid", style='TagInfo.TFrame')
            frame_tag.pack(fill=tk.X, pady=2, padx=2)
            
            ttk.Label(frame_tag, text=tag, padding=3).pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Button to Remove Tag from Photo
            ttk.Button(frame_tag, 
                       text="X", 
                       width=3, 
                       style='Danger.TButton',
                       command=lambda t=tag: self.aksi_hapus_tag_foto(t)
                       ).pack(side=tk.RIGHT)

    def aksi_hapus_tag_foto(self, tag_yang_dihapus):
        
        if not self.koleksi_foto: return

        foto_saat_ini = self.koleksi_foto[self.index_foto_saat_ini]
        if foto_saat_ini.hapus_tag(tag_yang_dihapus):            
            self.recalculate_unique_collection_tags()
            self.update_dropdown_photo_group()
            self.tampilkan_foto_saat_ini()
            
    def sebelumnya(self):
        if self.index_foto_saat_ini > 0:
            self.index_foto_saat_ini -= 1
            self.tampilkan_foto_saat_ini()
        else:
            messagebox.showinfo("Navigasi", "Ini adalah foto pertama.")

    def selanjutnya(self):
        if self.index_foto_saat_ini < len(self.koleksi_foto) - 1:
            self.index_foto_saat_ini += 1
            self.tampilkan_foto_saat_ini()
        else:
            messagebox.showinfo("Navigasi", "Ini adalah foto terakhir.")
            
    # --- Rating Logic Method ---
    def aksi_simpan_rating_base(self, nilai):
        """Basic logic for saving the rating."""
        if not self.koleksi_foto:
             messagebox.showwarning("Warning", "Tidak ada foto dalam koleksi.")
             return

        foto_saat_ini = self.koleksi_foto[self.index_foto_saat_ini]
        
        if foto_saat_ini.beri_rating(nilai):
            self.tampilkan_foto_saat_ini()

    def aksi_simpan_rating_tombol(self, nilai):
        self.aksi_simpan_rating_base(nilai)
        
    def aksi_simpan_rating_shortcut(self, nilai):
        # Karena event object dari shortcut diabaikan di base method, langsung panggil
        self.aksi_simpan_rating_base(nilai)
        

# ===============================================
# BAGIAN 3: EKSEKUSI PROGRAM
# ===============================================

if __name__ == "__main__":
    root = tk.Tk()
    
    # Style Configuration
    style = ttk.Style(root)
    # Use 'clam' for better styling control if available
    if 'clam' in style.theme_names():
        style.theme_use('clam')
        
    # --- Color Palette ---
    COLOR_ACCENT = '#4a86e8'
    COLOR_DANGER = '#dc3545'
    COLOR_TAG_BG = '#e6e6e6'
        
    # Main Button Style (Blue)
    style.configure('Accent.TButton', font=('Montserrat', 14, 'bold'), foreground='white', background=COLOR_ACCENT)
    style.map('Accent.TButton', background=[('active', '#3c78d8')])
    
    # Danger Button Style (Red)
    style.configure('Danger.TButton', font=('Montserrat', 8, 'bold'), foreground='white', background=COLOR_DANGER, borderwidth=0)
    style.map('Danger.TButton', background=[('active', '#c82333')])
    
    # Large Navigation Button Style
    style.configure('Big.TButton', font=('Montserrat', 16, 'bold'))
    
    # Tag Criteria Button Style (Clickable tags on the left)
    style.configure('Tag.TButton', font=('Montserrat', 10), background=COLOR_TAG_BG, foreground='#333333', borderwidth=0)
    style.map('Tag.TButton', background=[('active', '#cccccc')])
    
    style.configure('TagInfo.TFrame', background=COLOR_TAG_BG, relief="flat", borderwidth=0)

   root.configure(background="#f5f5f5")
    
    app = PhotoApp(root)
    root.mainloop()
