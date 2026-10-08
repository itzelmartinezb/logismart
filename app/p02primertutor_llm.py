"""Versión GUI del primer ejercicio: Tutor LLM con otro contexto y resumen de historial."""
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from app.config import settings
from app.services.llm_service import LLMService

SYSTEM = """Eres un tutor de programación orientado a proyectos de sistemas inteligentes y bases de datos. Ayuda con ejemplos prácticos, explica paso a paso, detecta errores y termina cada respuesta con una mini-recomendación de estudio. Evita hacer la tarea completa sin explicar."""

class TutorGUI(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Tutor LLM - LogiSmart"); self.geometry("950x650")
        self.llm=LLMService(settings.ollama_host,settings.ollama_model,settings.llm_timeout); self.history=[]
        self.output=tk.Text(self); self.output.pack(fill="both",expand=True,padx=10,pady=10)
        b=ttk.Frame(self); b.pack(fill="x",padx=10); self.q=ttk.Entry(b); self.q.pack(side="left",fill="x",expand=True); ttk.Button(b,text="Enviar",command=self.ask).pack(side="left",padx=5); ttk.Button(b,text="Resumen del historial",command=self.summary).pack(side="left")
        self.q.bind("<Return>",lambda e:self.ask())
    def ask(self):
        q=self.q.get().strip(); self.q.delete(0,"end")
        if not q:return
        self.history.append(("usuario",q)); self.output.insert("end",f"\nTú: {q}\nTutor: ...\n"); self.update_idletasks()
        def work():
            try:
                from ollama import Client
                c=Client(host=settings.ollama_host,timeout=settings.llm_timeout)
                msgs=[{"role":"system","content":SYSTEM}]+[{"role":"user" if r=="usuario" else "assistant","content":t} for r,t in self.history]
                ans=c.chat(model=settings.ollama_model,messages=msgs)["message"]["content"]
                self.history.append(("tutor",ans)); self.after(0,lambda:self._show(ans))
            except Exception as e:self.after(0,lambda:messagebox.showerror("Ollama",str(e)))
        threading.Thread(target=work,daemon=True).start()
    def _show(self,ans):
        self.output.insert("end",ans+"\n")
    def summary(self):
        if not self.history:return messagebox.showinfo("Historial","No hay interacciones todavía.")
        user=[x for r,x in self.history if r=="usuario"]
        self.output.insert("end",f"\n--- Resumen de historial ---\nPreguntas realizadas: {len(user)}\nTemas/preguntas recientes:\n"+"\n".join("• "+x[:140] for x in user[-5:])+"\n")

if __name__=="__main__": TutorGUI().mainloop()
