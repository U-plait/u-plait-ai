import ahocorasick
from sqlalchemy.orm import Session
from sqlalchemy import text

class BanwordFilter:
    def __init__(self, banwords: list[str]):
        self.automaton = ahocorasick.Automaton()
        for idx, word in enumerate(banwords):
            self.automaton.add_word(word, (idx, word))
        self.automaton.make_automaton()

    @classmethod
    def from_db(cls, db: Session):
        sql = text("SELECT ban_word FROM ban_word")
        result = db.execute(sql)
        banwords = [row[0] for row in result.fetchall()]
        return cls(banwords)

    def contains_banword(self, text: str) -> bool:
        return any(True for _ in self.automaton.iter(text))