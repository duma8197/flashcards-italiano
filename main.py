import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

import json
import random
import os
from datetime import datetime
import pandas as pd
try:
    from gtts import gTTS
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

class FlashcardsApp(App):
    def __init__(self):
        super().__init__()
        self.vocabulary = []
        self.current_session = []
        self.current_index = 0
        self.show_translation = False
        self.session_size = 5
        self.difficult_words = []
        
        # Storage per salvataggio dati
        self.data_store = JsonStore('flashcards_data.json')
        self.progress_store = JsonStore('user_progress.json')
        
        # Carica dati salvati
        self.load_data()
    
    def build(self):
        self.title = "🇮🇹 Flashcards Italiano"
        
        # Layout principale
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Header
        header = Label(
            text='🇮🇹 Flashcards Italiano-Inglese',
            font_size='24sp',
            size_hint_y=None,
            height='60dp',
            color=(0.2, 0.6, 1, 1)
        )
        main_layout.add_widget(header)
        
        # Info vocabolario
        self.vocab_info = Label(
            text=f'Vocabolario: {len(self.vocabulary)} parole',
            font_size='16sp',
            size_hint_y=None,
            height='40dp'
        )
        main_layout.add_widget(self.vocab_info)
        
        # Pulsanti gestione
        management_layout = GridLayout(cols=2, size_hint_y=None, height='60dp', spacing=10)
        
        load_btn = Button(
            text='📚 Carica Excel',
            background_color=(0.2, 0.7, 0.3, 1),
            font_size='16sp'
        )
        load_btn.bind(on_press=self.open_file_chooser)
        management_layout.add_widget(load_btn)
        
        clear_btn = Button(
            text='🗑️ Cancella Tutto',
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='16sp'
        )
        clear_btn.bind(on_press=self.clear_all_data)
        management_layout.add_widget(clear_btn)
        
        main_layout.add_widget(management_layout)
        
        # Configurazione sessione
        session_config = BoxLayout(orientation='horizontal', size_hint_y=None, height='60dp', spacing=10)
        
        session_config.add_widget(Label(text='Parole per sessione:', size_hint_x=0.4))
        
        self.session_slider = Slider(
            min=1, max=20, value=5, step=1,
            size_hint_x=0.4
        )
        self.session_slider.bind(value=self.on_session_size_change)
        session_config.add_widget(self.session_slider)
        
        self.session_size_label = Label(text='5', size_hint_x=0.2)
        session_config.add_widget(self.session_size_label)
        
        main_layout.add_widget(session_config)
        
        # Pulsante nuova sessione
        new_session_btn = Button(
            text='🚀 Nuova Sessione',
            background_color=(0.1, 0.5, 0.8, 1),
            size_hint_y=None,
            height='60dp',
            font_size='18sp'
        )
        new_session_btn.bind(on_press=self.start_new_session)
        main_layout.add_widget(new_session_btn)
        
        # Area flashcard
        self.flashcard_area = BoxLayout(orientation='vertical', spacing=15)
        main_layout.add_widget(self.flashcard_area)
        
        # Area progressi
        self.progress_area = BoxLayout(orientation='vertical', size_hint_y=None, height='100dp')
        main_layout.add_widget(self.progress_area)
        
        self.update_ui()
        return main_layout
    
    def load_data(self):
        """Carica dati salvati"""
        try:
            if self.data_store.exists('vocabulary'):
                self.vocabulary = self.data_store.get('vocabulary')['data']
            
            if self.data_store.exists('difficult_words'):
                self.difficult_words = self.data_store.get('difficult_words')['data']
        except:
            pass
    
    def save_data(self):
        """Salva dati"""
        try:
            self.data_store.put('vocabulary', data=self.vocabulary)
            self.data_store.put('difficult_words', data=self.difficult_words)
        except Exception as e:
            self.show_popup("Errore", f"Errore nel salvataggio: {e}")
    
    def on_session_size_change(self, instance, value):
        """Aggiorna dimensione sessione"""
        self.session_size = int(value)
        self.session_size_label.text = str(self.session_size)
    
    def open_file_chooser(self, instance):
        """Apri file chooser per Excel"""
        content = BoxLayout(orientation='vertical')
        
        if platform == 'android':
            # Su Android, mostra input manuale
            content.add_widget(Label(text='Inserisci il path del file Excel:', size_hint_y=None, height='40dp'))
            
            path_input = TextInput(
                text='/storage/emulated/0/Download/',
                multiline=False,
                size_hint_y=None,
                height='40dp'
            )
            content.add_widget(path_input)
            
            load_btn = Button(text='Carica File', size_hint_y=None, height='50dp')
            load_btn.bind(on_press=lambda x: self.load_excel_file(path_input.text))
            content.add_widget(load_btn)
        else:
            # Su desktop, usa file chooser
            filechooser = FileChooserIconView(filters=['*.xlsx', '*.xls'])
            content.add_widget(filechooser)
            
            load_btn = Button(text='Carica File Selezionato', size_hint_y=None, height='50dp')
            load_btn.bind(on_press=lambda x: self.load_excel_file(filechooser.selection[0] if filechooser.selection else None))
            content.add_widget(load_btn)
        
        popup = Popup(
            title='Carica File Excel',
            content=content,
            size_hint=(0.9, 0.9)
        )
        popup.open()
    
    def load_excel_file(self, filepath):
        """Carica file Excel"""
        if not filepath or not os.path.exists(filepath):
            self.show_popup("Errore", "File non trovato")
            return
        
        try:
            df = pd.read_excel(filepath)
            
            if 'Italian' not in df.columns or 'English' not in df.columns:
                self.show_popup("Errore", "Il file deve contenere colonne 'Italian' e 'English'")
                return
            
            # Pulisci e prepara dati
            df = df.dropna(subset=['Italian', 'English'])
            
            if 'Difficulty' not in df.columns:
                df['Difficulty'] = 'medio'
            
            new_words = df.to_dict('records')
            
            # Aggiungi al vocabolario esistente (rimuovi duplicati)
            existing_pairs = {(w['Italian'], w['English']) for w in self.vocabulary}
            unique_new_words = [w for w in new_words if (w['Italian'], w['English']) not in existing_pairs]
            
            self.vocabulary.extend(unique_new_words)
            self.save_data()
            
            self.show_popup("Successo", f"Caricate {len(unique_new_words)} nuove parole!")
            self.update_ui()
            
        except Exception as e:
            self.show_popup("Errore", f"Errore nel caricamento: {e}")
    
    def clear_all_data(self, instance):
        """Cancella tutti i dati"""
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Sei sicuro di voler cancellare tutti i dati?'))
        
        buttons = BoxLayout(size_hint_y=None, height='50dp')
        
        yes_btn = Button(text='Sì, Cancella', background_color=(0.8, 0.2, 0.2, 1))
        no_btn = Button(text='Annulla', background_color=(0.2, 0.6, 0.2, 1))
        
        popup = Popup(title='Conferma Cancellazione', content=content, size_hint=(0.8, 0.4))
        
        yes_btn.bind(on_press=lambda x: self.confirm_clear_data(popup))
        no_btn.bind(on_press=popup.dismiss)
        
        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        content.add_widget(buttons)
        
        popup.open()
    
    def confirm_clear_data(self, popup):
        """Conferma cancellazione dati"""
        self.vocabulary = []
        self.difficult_words = []
        self.current_session = []
        self.current_index = 0
        
        # Cancella file storage
        try:
            if os.path.exists('flashcards_data.json'):
                os.remove('flashcards_data.json')
            if os.path.exists('user_progress.json'):
                os.remove('user_progress.json')
        except:
            pass
        
        popup.dismiss()
        self.update_ui()
        self.show_popup("Completato", "Tutti i dati cancellati!")
    
    def start_new_session(self, instance):
        """Avvia nuova sessione"""
        if not self.vocabulary:
            self.show_popup("Errore", "Carica prima del vocabolario!")
            return
        
        # Seleziona parole casuali
        available_words = min(self.session_size, len(self.vocabulary))
        self.current_session = random.sample(self.vocabulary, available_words)
        self.current_index = 0
        self.show_translation = False
        
        self.update_flashcard_ui()
        self.show_popup("Sessione Avviata", f"Sessione con {len(self.current_session)} parole!")
    
    def update_ui(self):
        """Aggiorna interfaccia"""
        self.vocab_info.text = f'Vocabolario: {len(self.vocabulary)} parole | Difficili: {len(self.difficult_words)}'
        
        # Aggiorna slider massimo
        if self.vocabulary:
            self.session_slider.max = min(20, len(self.vocabulary))
        
        if not self.current_session:
            self.flashcard_area.clear_widgets()
            self.flashcard_area.add_widget(Label(text='Premi "Nuova Sessione" per iniziare', font_size='18sp'))
        else:
            self.update_flashcard_ui()
    
    def update_flashcard_ui(self):
        """Aggiorna UI flashcard"""
        self.flashcard_area.clear_widgets()
        
        if self.current_index >= len(self.current_session):
            # Sessione completata
            self.flashcard_area.add_widget(Label(text='🎉 Sessione Completata!', font_size='24sp', color=(0.2, 0.8, 0.2, 1)))
            
            new_session_btn = Button(
                text='🔄 Nuova Sessione',
                background_color=(0.1, 0.5, 0.8, 1),
                size_hint_y=None,
                height='60dp'
            )
            new_session_btn.bind(on_press=self.start_new_session)
            self.flashcard_area.add_widget(new_session_btn)
            return
        
        current_word = self.current_session[self.current_index]
        
        # Progress
        progress_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='30dp')
        progress_layout.add_widget(Label(text=f'Parola {self.current_index + 1} di {len(self.current_session)}', size_hint_x=0.7))
        
        progress_bar = ProgressBar(max=len(self.current_session), value=self.current_index + 1, size_hint_x=0.3)
        progress_layout.add_widget(progress_bar)
        self.flashcard_area.add_widget(progress_layout)
        
        # Parola italiana
        italian_card = Label(
            text=f"🇮🇹 {current_word['Italian']}",
            font_size='28sp',
            color=(1, 1, 1, 1),
            canvas_before=self.create_card_background((0.2, 0.4, 0.8, 1))
        )
        self.flashcard_area.add_widget(italian_card)
        
        # Audio italiano (se disponibile)
        if AUDIO_AVAILABLE:
            audio_btn = Button(
                text='🔊 Pronuncia Italiano',
                size_hint_y=None,
                height='50dp',
                background_color=(0.3, 0.6, 0.9, 1)
            )
            audio_btn.bind(on_press=lambda x: self.play_audio(current_word['Italian'], 'it'))
            self.flashcard_area.add_widget(audio_btn)
        
        if not self.show_translation:
            # Pulsante mostra traduzione
            show_btn = Button(
                text='👁️ Mostra Traduzione',
                background_color=(0.2, 0.7, 0.3, 1),
                size_hint_y=None,
                height='60dp',
                font_size='18sp'
            )
            show_btn.bind(on_press=self.show_translation_action)
            self.flashcard_area.add_widget(show_btn)
        else:
            # Mostra traduzione
            english_card = Label(
                text=f"🇬🇧 {current_word['English']}",
                font_size='24sp',
                color=(1, 1, 1, 1),
                canvas_before=self.create_card_background((0.2, 0.7, 0.3, 1))
            )
            self.flashcard_area.add_widget(english_card)
            
            # Audio inglese
            if AUDIO_AVAILABLE:
                audio_btn_en = Button(
                    text='🔊 Pronuncia Inglese',
                    size_hint_y=None,
                    height='50dp',
                    background_color=(0.3, 0.8, 0.4, 1)
                )
                audio_btn_en.bind(on_press=lambda x: self.play_audio(current_word['English'], 'en'))
                self.flashcard_area.add_widget(audio_btn_en)
            
            # Pulsanti valutazione
            self.add_rating_buttons(current_word)
    
    def create_card_background(self, color):
        """Crea background colorato per le carte"""
        from kivy.graphics import Color, Rectangle
        def draw_bg(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*color)
                Rectangle(pos=instance.pos, size=instance.size)
        return draw_bg
    
    def show_translation_action(self, instance):
        """Mostra traduzione"""
        self.show_translation = True
        self.update_flashcard_ui()
    
    def add_rating_buttons(self, word):
        """Aggiungi pulsanti di valutazione"""
        self.flashcard_area.add_widget(Label(text='Come valuti questa parola?', font_size='16sp'))
        
        rating_layout = GridLayout(cols=2, rows=2, spacing=10, size_hint_y=None, height='120dp')
        
        # Pulsante "La so!" (Verde)
        la_so_btn = Button(
            text='La so!',
            background_color=(0.2, 0.8, 0.2, 1),
            font_size='16sp'
        )
        la_so_btn.bind(on_press=lambda x: self.rate_word(word, "La so!"))
        rating_layout.add_widget(la_so_btn)
        
        # Pulsante "Facile" (Azzurro)
        facile_btn = Button(
            text='Facile',
            background_color=(0.1, 0.6, 0.8, 1),
            font_size='16sp'
        )
        facile_btn.bind(on_press=lambda x: self.rate_word(word, "Facile"))
        rating_layout.add_widget(facile_btn)
        
        # Pulsante "Difficile" (Giallo)
        difficile_btn = Button(
            text='Difficile',
            background_color=(0.9, 0.7, 0.1, 1),
            font_size='16sp'
        )
        difficile_btn.bind(on_press=lambda x: self.rate_word(word, "Difficile"))
        rating_layout.add_widget(difficile_btn)
        
        # Pulsante "Non la so" (Rosso)
        non_so_btn = Button(
            text='Non la so',
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='16sp'
        )
        non_so_btn.bind(on_press=lambda x: self.rate_word(word, "Non la so"))
        rating_layout.add_widget(non_so_btn)
        
        self.flashcard_area.add_widget(rating_layout)
    
    def rate_word(self, word, rating):
        """Valuta parola"""
        # Salva progresso
        word_key = f"{word['Italian']}-{word['English']}"
        
        try:
            if self.progress_store.exists(word_key):
                progress = self.progress_store.get(word_key)['data']
            else:
                progress = []
            
            progress.append({
                'rating': rating,
                'timestamp': datetime.now().isoformat()
            })
            
            self.progress_store.put(word_key, data=progress)
        except:
            pass
        
        # Gestisci parole difficili
        if rating in ['Difficile', 'Non la so']:
            if word not in self.difficult_words:
                self.difficult_words.append(word)
            
            # Se "Non la so", aggiungi alla fine della sessione
            if rating == "Non la so":
                self.current_session.append(word)
                self.show_popup("Ripasso", f"Parola '{word['Italian']}' aggiunta per ripasso!")
        
        self.save_data()
        
        # Prossima parola
        self.current_index += 1
        self.show_translation = False
        self.update_flashcard_ui()
    
    def play_audio(self, text, lang):
        """Riproduce audio"""
        if not AUDIO_AVAILABLE:
            self.show_popup("Audio non disponibile", "Installa pygame e gtts per l'audio")
            return
        
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save("temp_audio.mp3")
            
            pygame.mixer.init()
            pygame.mixer.music.load("temp_audio.mp3")
            pygame.mixer.music.play()
            
            # Rimuovi file temporaneo dopo un po'
            Clock.schedule_once(lambda dt: self.cleanup_audio(), 3)
            
        except Exception as e:
            self.show_popup("Errore Audio", f"Errore riproduzione: {e}")
    
    def cleanup_audio(self):
        """Pulisci file audio temporanei"""
        try:
            if os.path.exists("temp_audio.mp3"):
                os.remove("temp_audio.mp3")
        except:
            pass
    
    def show_popup(self, title, message):
        """Mostra popup informativo"""
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        
        close_btn = Button(text='OK', size_hint_y=None, height='50dp')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.open()

if __name__ == '__main__':
    FlashcardsApp().run()