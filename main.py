import asyncio
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from pydantic import ValidationError

from app import (
    Task,
    TaskCreate,
    UpdateTask,
    init_db,
    kill_engine,
    create_task,
    get_task,
    list_tasks,
    update_task,
    delete_task,
    get_session,
)


class TaskManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("800x600")
        self.selected_task_id: Optional[uuid.UUID] = None
        self.setup_ui()
        self.refresh_tasks()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Add New Task", padding="10")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(input_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.title_entry = ttk.Entry(input_frame, width=50)
        self.title_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(input_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.desc_entry = ttk.Entry(input_frame, width=50)
        self.desc_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Button(input_frame, text="Add Task", command=self.add_task).grid(row=2, column=1, sticky=tk.E, padx=5, pady=5)
        
        # Task list frame
        list_frame = ttk.LabelFrame(main_frame, text="Tasks", padding="10")
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        columns = ("id", "title", "description", "completed", "created_at")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("description", text="Description")
        self.tree.heading("completed", text="Completed")
        self.tree.heading("created_at", text="Created At")
        
        self.tree.column("id", width=250)
        self.tree.column("title", width=200)
        self.tree.column("description", width=200)
        self.tree.column("completed", width=80)
        self.tree.column("created_at", width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_task_select)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Refresh", command=self.refresh_tasks).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Mark Complete", command=self.mark_complete).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Task", command=self.edit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Task", command=self.delete_task).pack(side=tk.LEFT, padx=5)

    def on_task_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_task_id = uuid.UUID(item["values"][0])

    def refresh_tasks(self):
        try:
            tasks = asyncio.run(self._fetch_tasks())
            self._update_tree(tasks)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh tasks: {str(e)}")

    async def _fetch_tasks(self):
        async with get_session() as session:
            return await list_tasks(session)

    def _update_tree(self, tasks):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for task in tasks:
            self.tree.insert("", tk.END, values=(
                str(task.id),
                task.title,
                task.description or "",
                "Yes" if task.completed else "No",
                task.created_at.strftime("%Y-%m-%d %H:%M")
            ))

    def add_task(self):
        title = self.title_entry.get().strip()
        description = self.desc_entry.get().strip()
        
        if not title:
            messagebox.showwarning("Warning", "Title is required")
            return
        
        try:
            asyncio.run(self._create_task(title, description))
            self.title_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            self.refresh_tasks()
            messagebox.showinfo("Success", "Task added successfully")
        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add task: {str(e)}")

    async def _create_task(self, title: str, description: str):
        async with get_session() as session:
            task_data = TaskCreate(title=title, description=description if description else None)
            await create_task(session, task_data)

    def mark_complete(self):
        if not self.selected_task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return
        
        try:
            asyncio.run(self._update_task_completion(self.selected_task_id, True))
            self.refresh_tasks()
            messagebox.showinfo("Success", "Task marked as complete")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update task: {str(e)}")

    def edit_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Task")
        edit_window.geometry("400x300")
        
        ttk.Label(edit_window, text="Title:").pack(pady=5)
        title_entry = ttk.Entry(edit_window, width=40)
        title_entry.pack(pady=5)
        
        ttk.Label(edit_window, text="Description:").pack(pady=5)
        desc_entry = ttk.Entry(edit_window, width=40)
        desc_entry.pack(pady=5)
        
        def save_edit():
            title = title_entry.get().strip()
            description = desc_entry.get().strip()
            
            if not title:
                messagebox.showwarning("Warning", "Title is required")
                return
            
            try:
                asyncio.run(self._update_task(self.selected_task_id, title, description))
                edit_window.destroy()
                self.refresh_tasks()
                messagebox.showinfo("Success", "Task updated successfully")
            except ValidationError as e:
                messagebox.showerror("Validation Error", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update task: {str(e)}")
        
        ttk.Button(edit_window, text="Save", command=save_edit).pack(pady=10)

    async def _update_task_completion(self, task_id: uuid.UUID, completed: bool):
        async with get_session() as session:
            await update_task(session, task_id, UpdateTask(completed=completed))

    async def _update_task(self, task_id: uuid.UUID, title: str, description: str):
        async with get_session() as session:
            await update_task(session, task_id, UpdateTask(title=title, description=description if description else None))

    def delete_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Warning", "Please select a task")
            return
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this task?"):
            return
        
        try:
            success = asyncio.run(self._delete_task(self.selected_task_id))
            if success:
                self.refresh_tasks()
                messagebox.showinfo("Success", "Task deleted successfully")
            else:
                messagebox.showerror("Error", "Task not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete task: {str(e)}")

    async def _delete_task(self, task_id: uuid.UUID) -> bool:
        async with get_session() as session:
            return await delete_task(session, task_id)


async def main():
    await init_db()
    
    root = tk.Tk()
    app = TaskManagerApp(root)
    
    def on_closing():
        asyncio.run(kill_engine())
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    asyncio.run(main())
