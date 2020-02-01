import unittest

from utils.transliteration import transliterate


class TestTransliterate(unittest.TestCase):
    def test_english_string(self):
        original = 'The quick brown fox jumps over the lazy dog'
        result = transliterate(original)

        self.assertEqual(original, result)

    def test_english_string_with_punctuation_marks(self):
        original = 'Hello, world!'
        result = transliterate(original)

        self.assertEqual(original, result)

    def test_russian_string_with_punctuation_marks(self):
        result = transliterate('Привет, как дела?')

        self.assertEqual('Privet, kak dela?', result)

    def test_russian_string_with_soft_signs(self):
        result = transliterate('подъезд ель')

        self.assertEqual("pod'ezd el'", result)

    def test_russian_string_with_map_into_multiple_letters(self):
        result = transliterate('Щелкунчик и друзья')

        self.assertEqual("Schelkunchik i druz'ya", result)

    def test_russian_string_with_all_letters(self):
        result = transliterate('Съешь ещё этих мягких французских булок, да выпей чаю')

        self.assertEqual("S'esh' eschyo etih myagkih frantsuzskih bulok, da vypey chayu", result)

    def test_german_string_with_special_characters(self):
        result = transliterate('Äpfel schöne Grüße')

        self.assertEqual('Aepfel schoene Gruesse', result)

    def test_greek_string(self):
        result = transliterate('Θράσυλλος Ἑκατώνυµος καρακτηρ ῥυθμος')

        self.assertEqual('Thrasyllos Ekatonymos karakter rythmos', result)

    def test_remove_accents(self):
        result = transliterate('Montréal, Mère, Françoise')

        self.assertEqual('Montreal, Mere, Francoise', result)
