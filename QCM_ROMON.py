import tkinter as tk
from tkinter import messagebox
import os
from pathlib import Path
from google import genai
from google.genai import types
import threading
import re  

class My_App:
    def __init__(self, master):
        self.master = master
        self.master.title("Générateur de Questions - 1ère Année Bac")
        self.master.geometry("1110x700")
        self.master.minsize(800, 550) 
        
        # Couleurs sombres modernes
        self.bg_color = "#1E1E2E"
        self.frame_color = "#272733"     
        self.fg_color = "#CDD6F4"      
        self.btn_color = "#313244"     
        self.btn_hover = "#45475A"     
        self.ans_color = "#A6E3A1"     
        self.accent_color = "#5E7394"  

        self.master.configure(bg=self.bg_color)
        
        self.hidden_answer = ""
        self.hidden_source = ""
        
        home_directory = Path.home()
        api_file_path = home_directory / ".QCM_ROMON_API_GEMINI"

        if api_file_path.exists():
            with open(api_file_path, "r") as file:
                self.API_KEY = file.read().strip()
        else:
            messagebox.showerror("Erreur", f"Le fichier caché est introuvable dans :\n{api_file_path}")
            self.master.destroy()
            return

        try:
            self.client = genai.Client(api_key=self.API_KEY)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur d'initialisation du client :\n{e}")
            self.master.destroy()
            return


        #=============== Frame and Buttons and Labels ===============

        self.left_frame = tk.Frame(master, bg=self.frame_color, width=100, height=40)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Le frame principal qui contiendra tout sur le côté droit
        self.basic_frame = tk.Frame(master, bg=self.bg_color)
        self.basic_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.label_QCM = tk.Label(self.basic_frame, text="", font=("Arial", 13), wraplength=600, justify=tk.CENTER, bg=self.bg_color, fg=self.fg_color)
        
        self.button_show_answer = tk.Button(self.basic_frame, text="Afficher la réponse", cursor="hand2", command=self.show_answer, state=tk.DISABLED, font=("Arial", 12, "bold"), bg=self.accent_color, fg="#11111B", activebackground=self.btn_hover, activeforeground=self.fg_color, relief=tk.FLAT, width=25, pady=8)
        
        self.label_Answer = tk.Label(self.basic_frame, text="", font=("Arial", 12, "bold"), fg=self.fg_color, bg=self.bg_color)

        self.answer_frame = tk.Frame(self.basic_frame, bg=self.bg_color)

        self.scrollbar = tk.Scrollbar(self.answer_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.answer_text = tk.Text(self.answer_frame, height=8, width=75, wrap=tk.WORD, yscrollcommand=self.scrollbar.set, font=("Arial", 11), bg=self.bg_color, fg=self.ans_color, relief=tk.FLAT, state=tk.DISABLED)
        self.answer_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar.config(command=self.answer_text.yview)

        button_style = {
            "font": ("Arial", 11, "bold"), 
            "bg": self.btn_color, 
            "fg": self.fg_color, 
            "activebackground": self.btn_hover, 
            "activeforeground": self.fg_color, 
            "relief": tk.FLAT, 
            "width": 32, 
            "pady": 8
        }

        romon = tk.Label(self.left_frame, text="Choisissez le roman \n pour générer une question", font=("Arial", 14, "bold"), bg=self.frame_color, fg=self.fg_color)
        romon.pack(pady=15)

        self.button_la_boite_a_merveille = tk.Button(self.left_frame, text="La Boîte à Merveilles", cursor="hand2", command=lambda: self.generate_question("La Boîte à Merveilles"), **button_style)
        self.button_la_boite_a_merveille.pack(pady=6)
        
        self.button_antigone = tk.Button(self.left_frame, text="Antigone", cursor="hand2", command=lambda: self.generate_question("Antigone"), **button_style)
        self.button_antigone.pack(pady=6)
        
        self.button_le_dernier_jour_d_un_condamne = tk.Button(self.left_frame, text="Le Dernier Jour d'un Condamné", cursor="hand2", command=lambda: self.generate_question("Le Dernier Jour d'un Condamné"), **button_style)
        self.button_le_dernier_jour_d_un_condamne.pack(pady=6)

        # Message de bienvenue au début
        self.label_wilcome = tk.Label(self.basic_frame, text="📚 Prêt pour l'examen ?\n🎯 Choisissez un roman pour commencer.", 
                                    font=("Helvetica", 20, "bold"), 
                                    wraplength=650, 
                                    justify=tk.CENTER, 
                                    bg=self.bg_color, 
                                    fg=self.fg_color
        )
        self.label_wilcome.pack(pady=20)

    def safe_update_ui(self, target_widget, **kwargs):
        self.master.after(0, lambda: target_widget.config(**kwargs))

    def generate_question(self, novel_name):
        if self.label_wilcome.winfo_exists():
            self.label_wilcome.pack_forget()
            
        self.label_QCM.pack(pady=20, fill=tk.X)
        self.button_show_answer.pack(pady=15)
        self.label_Answer.pack(pady=5)
        self.answer_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.label_QCM.config(text="🔍 Recherche dans les sources éducatives réelles en cours...")
        self.label_Answer.config(text="") 
        
        self.answer_text.config(state=tk.NORMAL)
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.config(state=tk.DISABLED)
        
        self.button_show_answer.config(state=tk.DISABLED) 
        
        def api_worker():
            prompt = (
                f"Tu es un professeur de français expert, spécialisé dans la préparation "
                f"au baccalauréat marocain (1ère année Bac).\n\n"
                f"TÂCHE : Recherche sur Internet une VRAIE question d'examen ou d'exercice "
                f"provenant d'un site éducatif marocain fiable, concernant le roman "
                f"'{novel_name}'.\n\n"
                "CONTRAINTES STRICTES :\n"
                "- Une seule question, de type analysis littéraire ou comprehension.\n"
                "- Si aucune source fiable n'est trouvée, indique-le clairement au lieu "
                "d'inventer une question.\n"
                "- N'écris RIEN en dehors des balises ci-dessous.\n\n"
                "FORMAT DE SORTIE (obligatoire, respecte exactement) :\n"
                "[QUESTION] ... [/QUESTION]\n"
                "[ANSWER] ... [/ANSWER]\n"
                "[SOURCE] ... [/SOURCE]\n\n"
                "EXEMPLE :\n"
                "[QUESTION] Quel est le rôle du personnage de Lalla Zoubida dans "
                "La Boîte à Merveilles ? [/QUESTION]\n"
                "[ANSWER] Elle représente... [/ANSWER]\n"
                "[SOURCE] alloschool.com [/SOURCE]"
            )               

            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,  
                        response_mime_type="text/plain", 
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
            
                response_text = response.text
                
                question_match = re.search(r'\[QUESTION\](.*?)\[/QUESTION\]', response_text, re.DOTALL)
                answer_match = re.search(r'\[ANSWER\](.*?)\[/ANSWER\]', response_text, re.DOTALL)
                source_match = re.search(r'\[SOURCE\](.*?)\[/SOURCE\]', response_text, re.DOTALL)
                
                if question_match and answer_match:
                    question_part = question_match.group(1).strip()
                    self.hidden_answer = answer_match.group(1).strip() 
                    source_text = source_match.group(1).strip() if source_match else ""
                    
                    grounding_info = self._extract_grounding_sources(response)
                    
                    final_source = source_text
                    if grounding_info:
                        if final_source: final_source += "\n\n"
                        final_source += "📚 Sources trouvées via Google :\n" + grounding_info
                    
                    self.hidden_source = final_source
                    
                    self.safe_update_ui(self.label_QCM, text=question_part)
                    self.safe_update_ui(self.button_show_answer, state=tk.NORMAL)
                else:
                    self.safe_update_ui(self.label_QCM, text="❌ Erreur de formatage des balises, veuillez réessayer.")
                    
            except Exception as e:
                # Analyse intelligente de l'erreur pour afficher des messages compréhensibles en français
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    friendly_error = "⚠️ Vous avez dépassé la limite de requêtes par minute (Rate Limit).\nVeuillez attendre une minute complète avant de choisir un autre roman et de générer une nouvelle question."
                elif "network" in error_msg.lower() or "connection" in error_msg.lower() or "http" in error_msg.lower():
                    friendly_error = "❌ Erreur de connexion : Le programme n'a pas pu contacter le serveur.\nVeuillez vérifier votre connexion Internet et réessayer."
                elif "api_key" in error_msg.lower() or "invalid" in error_msg.lower():
                    friendly_error = "❌ Votre clé API est incorrecte ou a expiré. Veuillez vérifier votre fichier caché."
                else:
                    friendly_error = f"❌ Une erreur inattendue est survenue lors de l'exécution de votre requête :\n{error_msg}"
                
                self.safe_update_ui(self.label_QCM, text=friendly_error)

        threading.Thread(target=api_worker, daemon=True).start()

    def _extract_grounding_sources(self, response):
        sources = []
        try:
            if response.candidates and len(response.candidates) > 0:
                metadata = response.candidates[0].grounding_metadata
                if metadata and metadata.grounding_chunks:
                    for chunk in metadata.grounding_chunks:
                        if chunk.web:
                            title = chunk.web.title or "Source"
                            uri = chunk.web.uri or ""
                            sources.append(f"• {title}\n  {uri}")
        except Exception as e:
            print(f"⚠️ Impossible d'extraire les sources : {e}")
        return "\n".join(sources) if sources else ""

    def show_answer(self):
        if self.hidden_answer:
            self.label_Answer.config(text="Réponse :")
            content = self.hidden_answer
            if self.hidden_source:
                content += "\n\n" + "="*50 + "\n" + self.hidden_source
            
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.delete("1.0", tk.END) 
            self.answer_text.insert(tk.END, content)
            self.answer_text.config(state=tk.DISABLED)

# Fonction de protection globale pour capturer les erreurs de l'interface et des callbacks
def show_error(exc, val, tb):
    import traceback
    error_details = "".join(traceback.format_exception(exc, val, tb))
    messagebox.showerror("Erreur interne du système", f"Une erreur inattendue est survenue dans l'interface :\n{val}\n\nDétails techniques de l'erreur :\n{error_details}")

if __name__ == "__main__":
    root = tk.Tk()
    root.report_callback_exception = show_error  # Activation de la sécurité globale de l'interface
    app = My_App(root)
    root.mainloop()