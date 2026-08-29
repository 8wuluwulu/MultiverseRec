from typing import List, Optional
from multiverserec.models.Content import Content

class Book(Content):
    
    def __init__(self, title: str, author: str, description: str, genres: List[str], pages: int, rating: Optional[float] = None):
        super().__init__(title, description, genres, rating)
        self.author = author
        self.pages = pages
        
    def get_searchable_text(self) -> str:
        """Объединяем все текстовые поля для эмбеддинга в один текст"""
        return f"{self.title} {self.author} {self.description} {' '.join(self.genres)}"

    def get_content_type(self) -> str:
        return "book"
    
    def get_display_name(self) -> str:
        return f"{self.title} by {self.author}"

    def get_metadata(self) -> dict:
        base_metadata = super().get_metadata()
        base_metadata.update({
            "author": self.author,
            "pages": self.pages,
        })
        return base_metadata
        
        