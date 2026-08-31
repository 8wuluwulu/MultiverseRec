from typing import Optional
from multiverserec.models.Content import Content

class Movie:
    @staticmethod
    def create(title: str, director: str, description: str, genres: list[str], year: int, duration: Optional[int] = None, actors: Optional[list[str]] = None, country: Optional[str] = None, rating: Optional[float] = None, embedding: Optional[list[float]] = None) -> Content:
        return Content(
            title=title,
            description=description,
            content_type='movie',
            rating=rating,
            embedding=embedding,
            meta={
                "director": director,
                "genres": genres,
                "year": year,
                "duration": duration,
                "actors": actors or [],
                "country": country,
            }
        )
    
    @staticmethod
    def find_searchable_text(title: str, director: str, description: str, genres: list[str]) -> str:
        """Текст, который превращается в вектор"""
        return f"{title} {director} {description} {' '.join(genres)}"
        