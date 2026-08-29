from typing import List, Optional
from multiverserec.models.Content import Content

class Movie(Content):
    def __init__(self, title: str, director: str, description: str, genres: List[str], year: int, rating: Optional[float] = None):
        super().__init__(title, description, genres, rating)
        self.director = director
        self.year = year
        
    def get_searchable_text(self) -> str:
        return f"{self.title} {self.director} {self.description} {' '.join(self.genres)}"
    
    def get_content_type(self) -> str:
        return "movie"
    
    def get_display_name(self) -> str:
        return f"{self.title} ({self.year})"
    
    def get_metadata(self) -> dict:
        base_metadata = super().get_metadata()
        base_metadata.update({
            "director": self.director,
            "year": self.year
        })
        return base_metadata
    