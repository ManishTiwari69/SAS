"""
manage_admins.py
────────────────
Super Admin only — full CRUD on admin accounts + face retrain for any admin.

RBAC rules
──────────
  • Super cannot deactivate themselves if they are the LAST active Super.
  • Super cannot delete themselves.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_db_connection
from session   import user_session

PRIMARY = "#00d084"
BG      = "#f8f9fa"


def show_manage_admins(container, current_admin_id, on_back):
    """Entry-point called from main.py."""

    # Defence-in-depth check
    if not user_session.is_super:
        tk.Label(container,
                 text="🚫  Access Denied\nOnly Super Admins can manage accounts.",
                 font=("Arial", 14), fg="#e74c3c", bg=BG).pack(expand=True)
        return

    # ── title bar ─────────────────────────────────────────────────────
    top = tk.Frame(container, bg=BG)
    top.pack(fill="x", padx=30, pady=(22, 6))

    tk.Label(top, text="👥  Manage Admin Accounts",
             font=("Arial", 17, "bold"), bg=BG, fg="#1a1c23").pack(side="left")

    tk.Button(top, text="＋  Add New Admin",
              bg=PRIMARY, fg="white",
              font=("Arial", 10, "bold"), relief="flat",
              padx=14, pady=7, cursor="hand2",
              command=lambda: _open_add(container, current_admin_id, on_back)
              ).pack(side="right")

    # ── filter bar ────────────────────────────────────────────────────
    fb = tk.Frame(container, bg=BG)
    fb.pack(fill="x", padx=30, pady=(0, 8))

    tk.Label(fb, text="Role:",   bg=BG, font=("Arial", 10)).pack(side="left")
    role_var = tk.StringVar(value="All")
    ttk.Combobox(fb, textvariable=role_var,
                 values=["All", "Super", "Teacher"],
                 width=10, state="readonly").pack(side="left", padx=(4, 14))

    tk.Label(fb, text="Status:", bg=BG, font=("Arial", 10)).pack(side="left")
    status_var = tk.StringVar(value="All")
    ttk.Combobox(fb, textvariable=status_var,
                 values=["All", "active", "inactive"],
                 width=10, state="readonly").pack(side="left", padx=(4, 14))

    tk.Button(fb, text="Apply Filter",
              bg="#3498db", fg="white",
              font=("Arial", 9, "bold"), relief="flat",
              padx=10, pady=4, cursor="hand2",
              command=lambda: _reload(role_var.get(), status_var.get())
              ).pack(side="left")

    # ── table ─────────────────────────────────────────────────────────
    tw = tk.Frame(container, bg="white",
                  highlightthickness=1, highlightbackground="#ddd")
    tw.pack(fill="both", expand=True, padx=30, pady=(0, 8))

    style = ttk.Style()
    style.configure("Adm.Treeview",
                    background="white", foreground="#333",
                    rowheight=34, fieldbackground="white",
                    font=("Arial", 10))
    style.configure("Adm.Treeview.Heading",
                    font=("Arial", 10, "bold"), background="#f4f4f4")
    style.map("Adm.Treeview", background=[("selected", PRIMARY)])

    cols = ("ID", "Username", "Name", "Email", "Phone", "Role", "Status")
    tree = ttk.Treeview(tw, columns=cols, show="headings", style="Adm.Treeview")

    widths = {"ID": 45, "Username": 130, "Name": 180,
              "Email": 190, "Phone": 110, "Role": 80, "Status": 80}
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="center", width=widths[c])

    tree.tag_configure("active",   foreground="#27ae60")
    tree.tag_configure("inactive", foreground="#e74c3c")
    tree.tag_configure("Super",    font=("Arial", 10, "bold"))

    vsb = ttk.Scrollbar(tw, orient="vertical", command=tree.yview)
    tree.configure(yscroll=vsb.set)
    tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    vsb.pack(side="right", fill="y", pady=8, padx=(0, 8))

    # ── action bar ────────────────────────────────────────────────────
    ab = tk.Frame(container, bg=BG)
    ab.pack(fill="x", padx=30, pady=(0, 16))

    def _btn(text, bg, cmd):
        tk.Button(ab, text=text, bg=bg, fg="white",
                  font=("Arial", 10, "bold"), relief="flat",
                  padx=16, pady=8, cursor="hand2",
                  command=cmd).pack(side="left", padx=(0, 8))

    _btn("✏️  Edit Profile",
         "#3498db",
         lambda: _edit_selected(tree, container, current_admin_id, on_back))

    _btn("🧬  Retrain Face",
         "#e67e22",
         lambda: _retrain_selected(tree, container, current_admin_id, on_back))

    _btn("🔒  Deactivate",
         "#e67e22",
         lambda: _toggle_status(tree, current_admin_id, "inactive",
                                lambda: _reload(role_var.get(), status_var.get())))

    _btn("🔓  Activate",
         PRIMARY,
         lambda: _toggle_status(tree, current_admin_id, "active",
                                lambda: _reload(role_var.get(), status_var.get())))

    _btn("🗑️  Delete",
         "#e74c3c",
         lambda: _delete_selected(tree, current_admin_id,
                                  lambda: _reload(role_var.get(), status_var.get())))

    tk.Label(ab, text="Select a row first",
             font=("Arial", 9), bg=BG, fg="#aaa").pack(side="right")

    # ── loader ────────────────────────────────────────────────────────
    def _reload(role_f="All", status_f="All"):
        for r in tree.get_children():
            tree.delete(r)
        try:
            db     = get_db_connection()
            cursor = db.cursor()
            cursor.execute("""
                SELECT a.admin_id, a.username,
                       CONCAT(d.first_name,' ',d.last_name),
                       d.email, d.phone_no, a.role, a.status
                FROM admins a
                JOIN admin_details d ON a.admin_id = d.admin_id
                WHERE (%s='All' OR a.role=%s)
                  AND (%s='All' OR a.status=%s)
                ORDER BY a.role DESC, a.username
            """, (role_f, role_f, status_f, status_f))
            for row in cursor.fetchall():
                tags = [row[6]]
                if row[5] == "Super":
                    tags.append("Super")
                tree.insert("", "end", values=row, tags=tuple(tags))
            db.close()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    _reload()


# ── helpers ────────────────────────────────────────────────────────────

def _selected(tree):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("No Selection", "Select an admin first.")
        return None
    return tree.item(sel[0])["values"]


def _count_active_supers():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM admins WHERE role='Super' AND status='active'")
        n = cursor.fetchone()[0]
        db.close()
        return n
    except Exception:
        return 0


def _toggle_status(tree, current_admin_id, new_status, reload_fn):
    row = _selected(tree)
    if not row:
        return
    target_id, _, target_name, _, _, target_role, _ = row

    if (new_status == "inactive"
            and int(target_id) == int(current_admin_id)
            and target_role == "Super"
            and _count_active_supers() <= 1):
        messagebox.showerror(
            "Cannot Deactivate",
            "You are the only active Super Admin.\n"
            "Promote another admin to Super first.")
        return

    verb = "deactivate" if new_status == "inactive" else "activate"
    if not messagebox.askyesno("Confirm",
                                f"{verb.capitalize()} account for {target_name}?"):
        return

    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE admins SET status=%s WHERE admin_id=%s",
                       (new_status, target_id))
        db.commit()
        db.close()
        messagebox.showinfo("Done", f"Account {new_status}.")
        reload_fn()
    except Exception as e:
        messagebox.showerror("DB Error", str(e))


def _delete_selected(tree, current_admin_id, reload_fn):
    row = _selected(tree)
    if not row:
        return
    target_id, _, target_name, _, _, target_role, _ = row

    if int(target_id) == int(current_admin_id):
        messagebox.showerror("Error", "You cannot delete your own account.")
        return

    if target_role == "Super" and _count_active_supers() <= 1:
        messagebox.showerror(
            "Cannot Delete",
            "This is the only active Super Admin.")
        return

    if not messagebox.askyesno(
            "⚠️  Confirm Delete",
            f"Permanently delete '{target_name}'?\nThis cannot be undone."):
        return

    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM admin_details WHERE admin_id=%s", (target_id,))
        cursor.execute("DELETE FROM admins WHERE admin_id=%s",        (target_id,))
        db.commit()
        db.close()
        messagebox.showinfo("Deleted", f"Admin '{target_name}' removed.")
        reload_fn()
    except Exception as e:
        messagebox.showerror("DB Error", str(e))


def _edit_selected(tree, container, current_admin_id, on_back):
    row = _selected(tree)
    if not row:
        return
    target_id = row[0]
    from edit_admin import edit_admin
    for w in container.winfo_children():
        w.destroy()
    edit_admin(container, int(target_id),
               lambda: show_manage_admins(container, current_admin_id, on_back),
               allow_role_change=True)


def _retrain_selected(tree, container, current_admin_id, on_back):
    """Open edit_admin pre-scrolled to the Retrain Face section."""
    # Same as edit, but the retrain button is already visible there.
    _edit_selected(tree, container, current_admin_id, on_back)


def _open_add(container, current_admin_id, on_back):
    import admin_register
    for w in container.winfo_children():
        w.destroy()
    admin_register.register_admin(
        container,
        on_done=lambda: show_manage_admins(container, current_admin_id, on_back))
