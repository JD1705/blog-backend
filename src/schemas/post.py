from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from enum import Enum

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
