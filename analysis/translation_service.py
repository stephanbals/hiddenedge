if __name__ == "__main__":
    print("HiddenEdge Engine v1.0 | SB3PM")
# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
#
# This code is proprietary and confidential.
# Unauthorized use, distribution, or replication is prohibited.
# =========================================

# =========================================
# AIJobHunter V4 - Translation Service
# Normalizes any input language to English
# =========================================

from deep_translator import GoogleTranslator


class TranslationService:

    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')

    def translate_to_english(self, text: str) -> str:
        """
        Translate any input text to English.
        Safe fallback: returns original text if translation fails.
        """

        if not text or len(text.strip()) == 0:
            return text

        try:
            # GoogleTranslator has length limits → split if needed
            chunks = self._split_text(text, max_length=4000)

            translated_chunks = []

            for chunk in chunks:
                translated = self.translator.translate(chunk)
                translated_chunks.append(translated)

            return "\n".join(translated_chunks)

        except Exception as e:
            print(f"[Translation WARNING] {e}")
            return text  # fallback


    def _split_text(self, text: str, max_length: int = 4000):
        """
        Splits text into safe chunks for translation API
        """

        words = text.split()
        chunks = []
        current = []

        current_length = 0

        for word in words:
            if current_length + len(word) + 1 > max_length:
                chunks.append(" ".join(current))
                current = [word]
                current_length = len(word)
            else:
                current.append(word)
                current_length += len(word) + 1

        if current:
            chunks.append(" ".join(current))

        return chunks