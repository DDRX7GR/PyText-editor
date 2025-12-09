import tkinter as tk
from tkinter import filedialog, messagebox, font, ttk
import importlib.util
import shutil
import json
import os
import inspect
from pathlib import Path
import tempfile
import time


# Application state (document path, dirty flag, root reference)
APP_ROOT = None
CURRENT_PATH = None
IS_DIRTY = False
SESSION_FILE = Path.home() / '.pytext_session.json'
RETURN_FROM_PREVIOUS = False


def update_title(event=None):
    """Module-level stub. Replaced by UI `update_title` inside `main()` at runtime."""
    return


def new_file(text_widget):
    # This function now only clears the text; saving prompt handled by caller
    text_widget.delete("1.0", tk.END)
    global CURRENT_PATH, IS_DIRTY
    CURRENT_PATH = None
    IS_DIRTY = False
    if APP_ROOT:
        update_title()


def open_file(text_widget):
    global CURRENT_PATH, IS_DIRTY
    if not prompt_save_if_dirty(text_widget):
        return
    path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if not path:
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    text_widget.delete("1.0", tk.END)
    text_widget.insert(tk.END, content)
    CURRENT_PATH = path
    IS_DIRTY = False
    update_title()


def save_file(text_widget):
    global CURRENT_PATH, IS_DIRTY
    # If we already have a path, save directly
    if CURRENT_PATH:
        path = CURRENT_PATH
    else:
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text Files", "*.txt")])
        if not path:
            return
    content = text_widget.get("1.0", tk.END)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    CURRENT_PATH = path
    IS_DIRTY = False
    update_title()
    messagebox.showinfo("Saved", f"File saved to {path}")


def prompt_save_if_dirty(text_widget):
    """If document is dirty, prompt user to save. Return True to continue, False to cancel."""
    global IS_DIRTY
    if not IS_DIRTY:
        return True
    resp = messagebox.askyesnocancel("Save changes?", "You have unsaved changes. Save before continuing?")
    if resp is None:
        return False
    if resp:
        save_file(text_widget)
    return True


def save_session():
    """Save current session (file path) to recovery file."""
    if CURRENT_PATH:
        try:
            with open(SESSION_FILE, 'w') as f:
                json.dump({'last_file': CURRENT_PATH}, f)
        except Exception:
            pass


def load_session():
    """Load last session (file path) if available."""
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_file')
        except Exception:
            pass
    return None


def clear_session():
    """Clear saved session."""
    if SESSION_FILE.exists():
        try:
            SESSION_FILE.unlink()
        except Exception:
            pass


def show_splash_screen():
    """Show a 5-second splash screen with the logo."""
    splash = tk.Tk()
    splash.title("PyText editor")
    splash.geometry("500x500")
    splash.resizable(False, False)
    
    # Set white background
    splash.config(bg='white')
    
    # Center the splash screen
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - (splash.winfo_width() // 2)
    y = (splash.winfo_screenheight() // 2) - (splash.winfo_height() // 2)
    splash.geometry(f"500x500+{x}+{y}")
    
    # Load and display logo
    logo_photo = None
    try:
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, 'logo.png')
        
        print(f"Looking for logo at: {logo_path}")
        print(f"Logo exists: {os.path.exists(logo_path)}")
        
        if os.path.exists(logo_path):
            from PIL import Image, ImageTk
            logo_img = Image.open(logo_path)
            print(f"Logo image size: {logo_img.size}")
            logo_img = logo_img.resize((200, 200), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(splash, image=logo_photo, bg='white')
            logo_label.image = logo_photo  # Keep reference
            logo_label.pack(pady=30, padx=20)
            print("Logo packed successfully")
    except Exception as e:
        print(f"Error loading logo: {e}")
        import traceback
        traceback.print_exc()
    
    # Add text
    title_label = tk.Label(splash, text="PyText editor", font=("Arial", 20, "bold"), bg='white')
    title_label.pack(pady=10)
    
    subtitle_label = tk.Label(splash, text="A simple Python text editor", font=("Arial", 12), bg='white')
    subtitle_label.pack(pady=5)
    
    # Close splash after 5 seconds
    splash.after(5000, splash.destroy)
    splash.mainloop()


def show_startup_dialog():
    """Show startup dialog with options to open previous, create new, open file, or exit."""
    startup_root = tk.Tk()
    startup_root.title("PyText editor - Welcome")
    # Make window larger so all buttons are visible and allow resizing
    startup_root.geometry("600x520")
    startup_root.minsize(420, 360)
    startup_root.resizable(True, True)
    
    # Load and display logo if available
    logo_path = Path(__file__).parent / 'logo.png'
    if logo_path.exists():
        try:
            from PIL import Image, ImageTk
            logo_img = Image.open(logo_path).resize((100, 100))
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(startup_root, image=logo_photo)
            logo_label.image = logo_photo  # Keep a reference
            logo_label.pack(pady=10)
        except Exception:
            pass
    
    # Title
    title = tk.Label(startup_root, text="PyText editor", font=("Arial", 18, "bold"))
    title.pack(pady=5)
    
    # Subtitle
    subtitle = tk.Label(startup_root, text="Choose an action:", font=("Arial", 10))
    subtitle.pack(pady=5)
    
    choice = tk.IntVar(value=-1)
    
    # Buttons frame (use expand so buttons are laid out clearly)
    frame = tk.Frame(startup_root)
    frame.pack(pady=20, expand=True, fill='both')
    
    last_file = load_session()
    
    # Option 1: Return from previous session
    if last_file and os.path.exists(last_file):
        btn1 = tk.Button(frame, text=f"Return from Previous Session\n({os.path.basename(last_file)})",
                         height=2, command=lambda: (choice.set(1), startup_root.destroy()))
        btn1.pack(pady=6, padx=20, fill='x')
        print(f"Startup: Return button shown for {last_file}")
    
    # Option 2: Create new file
    btn2 = tk.Button(frame, text="Create New File", height=2,
                     command=lambda: (choice.set(2), startup_root.destroy()))
    btn2.pack(pady=6, padx=20, fill='x')
    print("Startup: Create New button shown")
    
    # Option 3: Open file
    btn3 = tk.Button(frame, text="Open File", height=2,
                     command=lambda: (choice.set(3), startup_root.destroy()))
    btn3.pack(pady=6, padx=20, fill='x')
    print("Startup: Open File button shown")
    
    # Option 4: Exit
    btn4 = tk.Button(frame, text="Exit", height=2,
                     command=lambda: (choice.set(4), startup_root.destroy()))
    btn4.pack(pady=6, padx=20, fill='x')
    print("Startup: Exit button shown")
    
    startup_root.mainloop()
    return choice.get()


def word_count(content: str) -> int:
    return len(content.split())


def toggle_tag(text_widget, tag_name, font_kwargs):
    try:
        start = text_widget.index("sel.first")
        end = text_widget.index("sel.last")
    except tk.TclError:
        messagebox.showinfo("Selection required", "Select text to format.")
        return
    current_font = font.Font(text_widget, text_widget.cget("font"))
    current_font.configure(**font_kwargs)
    text_widget.tag_configure(tag_name, font=current_font)
    if text_widget.tag_nextrange(tag_name, start, end):
        text_widget.tag_remove(tag_name, start, end)
    else:
        text_widget.tag_add(tag_name, start, end)


def make_bold(text_widget):
    toggle_tag(text_widget, "bold", {"weight": "bold"})


def make_italic(text_widget):
    toggle_tag(text_widget, "italic", {"slant": "italic"})


def make_title(text_widget):
    # Apply to selection if present, otherwise to current line
    try:
        start = text_widget.index("sel.first")
        end = text_widget.index("sel.last")
    except tk.TclError:
        start = text_widget.index("insert linestart")
        end = text_widget.index("insert lineend")
    base_font = font.Font(text_widget, text_widget.cget("font"))
    title_font = font.Font(text_widget, text_widget.cget("font"))
    title_font.configure(size=base_font['size'] + 8, weight="bold")
    text_widget.tag_configure("title", font=title_font, justify="center")
    text_widget.tag_add("title", start, end)


def open_file_internal(file_path):
    """Internal function to open a file directly by path."""
    global CURRENT_PATH, IS_DIRTY
    if os.path.exists(file_path):
        try:
            text = find_text_widget()
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            text.delete("1.0", tk.END)
            text.insert(tk.END, content)
            CURRENT_PATH = file_path
            IS_DIRTY = False
            update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")


def install_update(root, text_widget, title_var):
    """Let user select a .py file and run its `apply_update` function if present.

    The update module should expose one of:
      - apply_update(app): a function that accepts an app-context dict and applies changes
      - This runs the code in the update file, so only install files you trust.
    """
    # Ask for confirmation (security warning)
    ok = messagebox.askyesno("Install Update",
                             "Install a Python update file (.py)?\n\nWARNING: This will execute code from the selected file. Only install updates you trust. Continue?")
    if not ok:
        return

    path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
    if not path:
        return

    # Optionally copy the update file to an updates/ folder for record
    updates_dir = Path(__file__).parent / 'updates'
    updates_dir.mkdir(exist_ok=True)
    try:
        dest = updates_dir / Path(path).name
        shutil.copy2(path, dest)
    except Exception:
        dest = None

    try:
        spec = importlib.util.spec_from_file_location("pytext_update", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        messagebox.showerror("Update Failed", f"Failed to load update file:\n{e}")
        return

    # Build a minimal app-context to pass to the update
    app_ctx = {
        'root': root,
        'text': text_widget,
        'title_var': title_var,
        'save_file': save_file,
        'open_file': open_file,
        'new_file': new_file,
        'make_bold': make_bold,
        'make_italic': make_italic,
        'make_title': make_title,
        'update_title': update_title,
        'CURRENT_PATH': lambda: CURRENT_PATH,
    }

    # Look for common callable entry points in the module (try several names)
    candidates = [name for name in ('apply_update', 'apply', 'update', 'main', 'install_update')
                  if hasattr(module, name) and callable(getattr(module, name))]
    try:
        if candidates:
            chosen = candidates[0]
            # Confirm before calling
            ok = messagebox.askyesno("Run update function",
                                     f"Found function `{chosen}` in the selected file. Run it now?\n\nThis function will be called with the app context and may modify the UI or files.")
            if not ok:
                messagebox.showinfo("Update Skipped", "Update function was not executed.")
                return
            func = getattr(module, chosen)
            # Inspect the callable's signature and call appropriately
            try:
                sig = inspect.signature(func)
                params = list(sig.parameters.values())
                # No parameters -> call directly
                if len(params) == 0:
                    func()
                # Single parameter -> pass the app context dict
                elif len(params) == 1:
                    func(app_ctx)
                else:
                    # Try to map common parameter names to values
                    mapping = {
                        'app': app_ctx,
                        'app_ctx': app_ctx,
                        'ctx': app_ctx,
                        'root': root,
                        'text': text_widget,
                        'title_var': title_var,
                        'save_file': save_file,
                        'open_file': open_file,
                        'new_file': new_file,
                        'make_bold': make_bold,
                        'make_italic': make_italic,
                        'make_title': make_title,
                        'update_title': update_title,
                    }
                    kwargs = {}
                    for p in params:
                        name = p.name
                        if name in mapping:
                            kwargs[name] = mapping[name]
                        elif name in ('app', 'app_ctx', 'ctx') and 'app' not in kwargs:
                            kwargs[name] = app_ctx
                    if kwargs:
                        func(**kwargs)
                    else:
                        # Fallback to passing app_ctx as single arg
                        func(app_ctx)
            except Exception:
                # If signature inspection fails for any reason, try the simple call
                func(app_ctx)
            messagebox.showinfo("Update Installed", "Update applied successfully.")
        else:
            # No callable update entry found — offer to show file contents and instructions
            show = messagebox.askyesno("No Update Action",
                                       "The selected file did not provide a callable update function like `apply_update(app)`.\n\nWould you like to view the file contents and instructions for creating an update file?")
            if show:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        src = f.read()
                except Exception:
                    src = "(Could not read file)"
                dlg = tk.Toplevel(root)
                dlg.title("Update file contents")
                txt = tk.Text(dlg, wrap='none', width=80, height=30)
                txt.insert('1.0', src)
                txt.config(state='disabled')
                txt.pack(expand=True, fill='both')
                info = tk.Label(dlg, text=("To be used as an update, the file should provide:\n"
                                           "def apply_update(app):\n    # modify app (app['root'], app['text'], etc.)\n"))
                info.pack(pady=6)
                tk.Button(dlg, text='Close', command=dlg.destroy).pack(pady=4)
            else:
                messagebox.showinfo("No Update Action", "No update function found; nothing was executed.")
    except Exception as e:
        messagebox.showerror("Update Error", f"Error while applying update:\n{e}")


def launch_offline_editor():
    """Launch the integrated offline editor UI defined in this file.

    The offline editor functions are prefixed with `offline_` to avoid name collisions.
    """
    try:
        root = offline_build_ui()
        root.mainloop()
    except NameError:
        messagebox.showerror("Offline Editor", "Offline editor code is not available.")
    except Exception as e:
        messagebox.showerror("Offline Editor", f"Failed to start offline editor:\n{e}")


# ----------------------- Integrated offline editor -----------------------
# The original `google_docs_offline.py` has been merged below with function
# names prefixed by `offline_` to avoid collisions with the main app.

OFF_APP_STATE = {
    'current_path': None,
    'is_dirty': False,
}

OFF_FONTS = [
    'Arial', 'Calibri', 'Times New Roman', 'Courier New', 'Verdana',
    'Georgia', 'Trebuchet MS', 'Comic Sans MS', 'Impact', 'Lucida Console'
]
OFF_SIZES = [str(s) for s in [8,9,10,11,12,14,16,18,20,22,24,26,28,32,36,38]]


def offline_prompt_save_if_dirty(root, text_widget):
    if not OFF_APP_STATE['is_dirty']:
        return True
    resp = messagebox.askyesnocancel('Save changes?', 'You have unsaved changes. Save now?')
    if resp is None:
        return False
    if resp:
        offline_save_file(root, text_widget)
    return True


def offline_new_file(root, text_widget, title_var):
    if not offline_prompt_save_if_dirty(root, text_widget):
        return
    text_widget.delete('1.0', tk.END)
    title_var.set('Untitled')
    OFF_APP_STATE['current_path'] = None
    OFF_APP_STATE['is_dirty'] = False
    offline_update_title(root, title_var)


def offline_open_file(root, text_widget, title_var):
    if not offline_prompt_save_if_dirty(root, text_widget):
        return
    path = filedialog.askopenfilename(filetypes=[('Text', '*.txt'), ('All files', '*.*')])
    if not path:
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        messagebox.showerror('Open error', str(e))
        return
    text_widget.delete('1.0', tk.END)
    text_widget.insert(tk.END, content)
    OFF_APP_STATE['current_path'] = path
    OFF_APP_STATE['is_dirty'] = False
    title_var.set(os.path.basename(path))
    offline_update_title(root, title_var)


def offline_save_file(root, text_widget):
    if OFF_APP_STATE['current_path']:
        path = OFF_APP_STATE['current_path']
    else:
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text', '*.txt')])
        if not path:
            return
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text_widget.get('1.0', tk.END))
    except Exception as e:
        messagebox.showerror('Save error', str(e))
        return
    OFF_APP_STATE['current_path'] = path
    OFF_APP_STATE['is_dirty'] = False
    offline_update_title(None, None)
    messagebox.showinfo('Saved', f'Saved to {path}')


def offline_save_file_as(root, text_widget):
    path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text', '*.txt')])
    if not path:
        return
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text_widget.get('1.0', tk.END))
    except Exception as e:
        messagebox.showerror('Save error', str(e))
        return
    OFF_APP_STATE['current_path'] = path
    OFF_APP_STATE['is_dirty'] = False
    offline_update_title(None, None)
    messagebox.showinfo('Saved', f'Saved to {path}')


def offline_update_title(root, title_var):
    name = ''
    if title_var:
        name = title_var.get()
    elif OFF_APP_STATE['current_path']:
        name = os.path.basename(OFF_APP_STATE['current_path'])
    else:
        name = 'Untitled'
    marker = ' •' if OFF_APP_STATE['is_dirty'] else ''
    if root:
        root.title(f'{name}{marker} - PyText (Offline)')


def offline_make_tag_name(props: dict):
    return f"f_{props.get('family')}_s_{props.get('size')}_w_{props.get('weight')}_sl_{props.get('slant')}_u_{int(props.get('underline'))}"


def offline_apply_font_tag(text, start, end, family, size, weight='normal', slant='roman', underline=False):
    props = {'family': family, 'size': size, 'weight': weight, 'slant': slant, 'underline': underline}
    tag = offline_make_tag_name(props)
    if not text.tag_cget(tag, 'font'):
        f = font.Font(family=family, size=size, weight=weight, slant=slant, underline=underline)
        text.tag_configure(tag, font=f)
    text.tag_add(tag, start, end)


def offline_toggle_tag(text, tag):
    try:
        start = text.index('sel.first')
        end = text.index('sel.last')
    except tk.TclError:
        messagebox.showinfo('Selection required', 'Select text to format.')
        return
    if text.tag_nextrange(tag, start, end):
        text.tag_remove(tag, start, end)
    else:
        text.tag_add(tag, start, end)


def offline_find_replace_dialog(root, text_widget):
    dlg = tk.Toplevel(root)
    dlg.title('Find and Replace')
    dlg.transient(root)
    tk.Label(dlg, text='Find:').grid(row=0, column=0, sticky='e')
    find_var = tk.StringVar()
    tk.Entry(dlg, textvariable=find_var, width=30).grid(row=0, column=1, padx=4, pady=4)
    tk.Label(dlg, text='Replace:').grid(row=1, column=0, sticky='e')
    replace_var = tk.StringVar()
    tk.Entry(dlg, textvariable=replace_var, width=30).grid(row=1, column=1, padx=4, pady=4)

    def do_find():
        text_widget.tag_remove('search', '1.0', tk.END)
        q = find_var.get()
        if not q:
            return
        idx = '1.0'
        while True:
            idx = text_widget.search(q, idx, nocase=1, stopindex=tk.END)
            if not idx:
                break
            lastidx = f"{idx}+{len(q)}c"
            text_widget.tag_add('search', idx, lastidx)
            idx = lastidx
        text_widget.tag_configure('search', background='yellow')

    def do_replace():
        q = find_var.get()
        r = replace_var.get()
        if not q:
            return
        content = text_widget.get('1.0', tk.END)
        content = content.replace(q, r)
        text_widget.delete('1.0', tk.END)
        text_widget.insert('1.0', content)
        OFF_APP_STATE['is_dirty'] = True

    tk.Button(dlg, text='Find', command=do_find).grid(row=2, column=0, pady=6)
    tk.Button(dlg, text='Replace All', command=do_replace).grid(row=2, column=1, pady=6)


def offline_word_count(text_widget):
    text = text_widget.get('1.0', tk.END)
    return len(text.split())


def offline_create_toolbar(root, text_widget, title_var):
    toolbar = tk.Frame(root)

    # Bold/Italic/Underline
    bold_btn = tk.Button(toolbar, text='B', width=3, command=lambda: offline_toggle_tag(text_widget, 'bold'))
    bold_btn.pack(side='left', padx=2)
    italic_btn = tk.Button(toolbar, text='I', width=3, command=lambda: offline_toggle_tag(text_widget, 'italic'))
    italic_btn.pack(side='left', padx=2)
    under_btn = tk.Button(toolbar, text='U', width=3, command=lambda: offline_toggle_tag(text_widget, 'underline'))
    under_btn.pack(side='left', padx=2)

    # Font family
    ttk.Label(toolbar, text='Font:').pack(side='left', padx=(10,2))
    font_combo = ttk.Combobox(toolbar, values=OFF_FONTS, width=20)
    font_combo.set(OFF_FONTS[0])
    font_combo.pack(side='left', padx=2)

    # Size
    ttk.Label(toolbar, text='Size:').pack(side='left', padx=(10,2))
    size_combo = ttk.Combobox(toolbar, values=OFF_SIZES, width=5)
    size_combo.set('12')
    size_combo.pack(side='left', padx=2)

    def apply_font():
        family = font_combo.get()
        size = int(size_combo.get())
        try:
            start = text_widget.index('sel.first')
            end = text_widget.index('sel.last')
        except tk.TclError:
            start = text_widget.index('insert linestart')
            end = text_widget.index('insert lineend')
        offline_apply_font_tag(text_widget, start, end, family, size)
        OFF_APP_STATE['is_dirty'] = True

    ttk.Button(toolbar, text='Apply Font', command=apply_font).pack(side='left', padx=6)

    # Alignment
    def align(direction):
        try:
            start = text_widget.index('sel.first')
            end = text_widget.index('sel.last')
        except tk.TclError:
            start = text_widget.index('insert linestart')
            end = text_widget.index('insert lineend')
        tag = f'align_{direction}'
        text_widget.tag_configure(tag, justify=direction)
        text_widget.tag_add(tag, start, end)
        OFF_APP_STATE['is_dirty'] = True

    ttk.Button(toolbar, text='Left', command=lambda: align('left')).pack(side='left', padx=2)
    ttk.Button(toolbar, text='Center', command=lambda: align('center')).pack(side='left', padx=2)
    ttk.Button(toolbar, text='Right', command=lambda: align('right')).pack(side='left', padx=2)

    return toolbar


def offline_start_autosave(root, text_widget):
    tmp = Path(tempfile.gettempdir()) / 'pytext_autosave.txt'
    def autosave():
        try:
            if OFF_APP_STATE['is_dirty'] and OFF_APP_STATE['current_path']:
                with open(OFF_APP_STATE['current_path'], 'w', encoding='utf-8') as f:
                    f.write(text_widget.get('1.0', tk.END))
                OFF_APP_STATE['is_dirty'] = False
            else:
                with open(tmp, 'w', encoding='utf-8') as f:
                    f.write(text_widget.get('1.0', tk.END))
        except Exception:
            pass
        root.after(25000, autosave)
    root.after(25000, autosave)


def offline_build_ui():
    root = tk.Tk()
    root.geometry('900x700')
    root.title('PyText (Offline)')

    title_var = tk.StringVar(value='Untitled')
    title_entry = tk.Entry(root, textvariable=title_var, font=('Arial', 16, 'bold'))
    title_entry.pack(fill='x', padx=8, pady=(8,0))

    text_frame = tk.Frame(root)
    text_frame.pack(expand=True, fill='both', padx=8, pady=8)
    text = tk.Text(text_frame, wrap='word', undo=True)
    text.pack(side='left', expand=True, fill='both')
    scrollbar = tk.Scrollbar(text_frame, command=text.yview)
    scrollbar.pack(side='right', fill='y')
    text.config(yscrollcommand=scrollbar.set)

    toolbar = offline_create_toolbar(root, text, title_var)
    toolbar.pack(fill='x', padx=8, pady=(0,4))

    menu = tk.Menu(root)
    root.config(menu=menu)
    file_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label='File', menu=file_menu)
    file_menu.add_command(label='New', command=lambda: offline_new_file(root, text, title_var))
    file_menu.add_command(label='Open', command=lambda: offline_open_file(root, text, title_var))
    file_menu.add_command(label='Save', command=lambda: offline_save_file(root, text))
    file_menu.add_command(label='Save As', command=lambda: offline_save_file_as(root, text))
    file_menu.add_separator()
    file_menu.add_command(label='Exit', command=lambda: (offline_prompt_save_if_dirty(root, text) and root.destroy()))

    edit_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label='Edit', menu=edit_menu)
    edit_menu.add_command(label='Undo', command=lambda: text.edit_undo())
    edit_menu.add_command(label='Redo', command=lambda: text.edit_redo())
    edit_menu.add_separator()
    edit_menu.add_command(label='Find/Replace', command=lambda: offline_find_replace_dialog(root, text))

    tools_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label='Tools', menu=tools_menu)
    tools_menu.add_command(label='Word Count', command=lambda: messagebox.showinfo('Word Count', f"{offline_word_count(text)} words"))

    help_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label='Help', menu=help_menu)
    help_menu.add_command(label='About', command=lambda: messagebox.showinfo('About', 'PyText Offline - Google Docs-like experience (no internet)'))

    def on_modified(event=None):
        if text.edit_modified():
            OFF_APP_STATE['is_dirty'] = True
            offline_update_title(root, title_var)
            text.edit_modified(False)
    text.bind('<<Modified>>', on_modified)

    offline_start_autosave(root, text)

    root.bind_all('<Control-s>', lambda e: (offline_save_file(root, text), 'break'))
    root.bind_all('<Control-b>', lambda e: (offline_toggle_tag(text, 'bold'), 'break'))
    root.bind_all('<Control-i>', lambda e: (offline_toggle_tag(text, 'italic'), 'break'))
    root.bind_all('<Control-u>', lambda e: (offline_toggle_tag(text, 'underline'), 'break'))

    return root

# --------------------- End integrated offline editor ---------------------


def find_text_widget():
    """Find the text widget from the app root."""
    for child in APP_ROOT.winfo_children():
        if isinstance(child, tk.Text):
            return child
        for subchild in child.winfo_children():
            if isinstance(subchild, tk.Text):
                return subchild
    return None


def main():
    root = tk.Tk()
    root.title("PyText editor")
    global APP_ROOT
    APP_ROOT = root
    
    # Set window icon if logo exists
    logo_path = Path(__file__).parent / 'logo.png'
    if logo_path.exists():
        try:
            from PIL import Image, ImageTk
            logo_img = Image.open(logo_path).resize((32, 32))
            logo_photo = ImageTk.PhotoImage(logo_img)
            root.iconphoto(False, logo_photo)
            root.icon_ref = logo_photo  # Keep a reference
        except Exception:
            pass

    # Title entry (like Google Docs)
    title_frame = tk.Frame(root)
    title_frame.pack(fill="x", padx=8, pady=(8, 0))
    title_var = tk.StringVar(value="Untitled")
    title_entry = tk.Entry(title_frame, textvariable=title_var, font=("Arial", 16, "bold"))
    title_entry.pack(fill="x")

    # Text area
    text = tk.Text(root, wrap="word", font=("Arial", 12))
    text.pack(expand=True, fill="both")

    def update_title(event=None):
        # set window title to show doc title and dirty marker
        name = title_var.get() or "Untitled"
        marker = "•" if IS_DIRTY else ""
        if CURRENT_PATH:
            display = f"{name} {marker} - {CURRENT_PATH} - PyText editor"
        else:
            display = f"{name} {marker} - PyText editor"
        root.title(display)

    # expose update_title for module-level calls
    globals()['update_title'] = update_title

    # Menu bar
    menu = tk.Menu(root)
    root.config(menu=menu)

    file_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="New", command=lambda: (prompt_save_if_dirty(text) and new_file(text) and update_title()))
    file_menu.add_command(label="Open", command=lambda: open_file(text))
    file_menu.add_command(label="Open Offline Editor", command=lambda: launch_offline_editor())
    file_menu.add_command(label="Install Update...", command=lambda: install_update(root, text, title_var))
    file_menu.add_command(label="Save", command=lambda: save_file(text))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)

    tools_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Tools", menu=tools_menu)
    tools_menu.add_command(
        label="Word Count",
        command=lambda: messagebox.showinfo("Word Count", f"{word_count(text.get('1.0', tk.END))} words")
    )

    help_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(
        label="About Developers",
        command=lambda: messagebox.showinfo("About", "PyText editor\n\nMade by Ohe")
    )

    # Basic formatting buttons
    toolbar = tk.Frame(root)
    toolbar.pack(fill="x")

    bold_btn = tk.Button(toolbar, text="Bold", command=lambda: make_bold(text))
    bold_btn.pack(side="left")

    italic_btn = tk.Button(toolbar, text="Italic", command=lambda: make_italic(text))
    italic_btn.pack(side="left")

    title_btn = tk.Button(toolbar, text="Title", command=lambda: make_title(text))
    title_btn.pack(side="left")

    update_btn = tk.Button(toolbar, text="Update", command=lambda: install_update(root, text, title_var))
    update_btn.pack(side="left")

    # Bindings: shortcuts like Google Docs (Ctrl+S, Ctrl+N, Ctrl+B, Ctrl+I)
    root.bind_all('<Control-s>', lambda e: (save_file(text), 'break'))
    root.bind_all('<Control-n>', lambda e: (prompt_save_if_dirty(text) and new_file(text) and update_title(), 'break'))
    root.bind_all('<Control-b>', lambda e: (make_bold(text), 'break'))
    root.bind_all('<Control-i>', lambda e: (make_italic(text), 'break'))

    # Track changes to mark document dirty and update title
    def on_modified(event=None):
        global IS_DIRTY
        if text.edit_modified():
            IS_DIRTY = True
            update_title()
            text.edit_modified(False)

    text.bind('<<Modified>>', on_modified)

    # Autosave (every 15 seconds) when document has a path
    def autosave():
        global IS_DIRTY, CURRENT_PATH
        if IS_DIRTY and CURRENT_PATH:
            try:
                # save silently
                content = text.get('1.0', tk.END)
                with open(CURRENT_PATH, 'w', encoding='utf-8') as f:
                    f.write(content)
                IS_DIRTY = False
                update_title()
            except Exception:
                pass
        root.after(15000, autosave)

    root.after(15000, autosave)

    # Prompt to save before closing
    def on_close():
        if not prompt_save_if_dirty(text):
            return
        save_session()  # Save session before closing
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)

    # Initialize title display
    update_title()

    root.mainloop()


if __name__ == "__main__":
    # Show splash screen for 5 seconds
    show_splash_screen()
    
    # Show startup dialog and handle user choice
    choice = show_startup_dialog()
    
    if choice == 1:  # Return from previous
        RETURN_FROM_PREVIOUS = True
        last_file = load_session()
        main()
        if last_file and os.path.exists(last_file):
            # Open the last file in a delayed callback
            APP_ROOT.after(100, lambda: open_file_internal(last_file))
    elif choice == 2:  # Create new
        RETURN_FROM_PREVIOUS = False
        clear_session()
        main()
    elif choice == 3:  # Open file
        RETURN_FROM_PREVIOUS = False
        clear_session()
        main()
        APP_ROOT.after(100, lambda: open_file(find_text_widget()))
    # choice == 4 or -1: Exit (do nothing)