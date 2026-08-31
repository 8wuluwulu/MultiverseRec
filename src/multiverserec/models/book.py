from typing import Optional
from multiverserec.models.Content import Content

class Book:
    @staticmethod
    def create(title: str, author: str, description: str, genres: list[str], pages: int, rating: Optional[float] = None, embedding: Optional[list[float]] = None) -> Content:
        return Content(
            title = title,
            description = description,
            content_type = 'book',
            rating = rating,
            embedding = embedding,
            meta ={
                "author": author,
                "genres": genres,
                "pages": pages,
            }
        )
    
    def get_searcheable_text(title: str, author: str, description: str, genres: list[str]) -> str:
        """Текст, который превращается в вектор"""
        return f"{title} {author} {description} {' '.join(genres)}"

    
        
    
        
        