"""
Notion API client wrapper for the Fitness & Diet Logger.
Uses direct HTTP requests with proper API version header.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import httpx

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import settings


class NotionLogger:
    """
    Wrapper for Notion API operations related to fitness and diet logging.
    Uses httpx with explicit Notion-Version header for compatibility.
    """

    API_BASE = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize the Notion client.

        Args:
            api_key: Notion API key. If not provided, uses environment variable.
            database_id: Notion database ID. If not provided, uses environment variable.
        """
        self.api_key = api_key or settings.NOTION_API_KEY
        self.database_id = database_id or settings.NOTION_DATABASE_ID

        if not self.api_key:
            raise ValueError(
                "Notion API key is required. Set NOTION_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.API_VERSION,
        }
        self._database_validated = False

    def _request(self, method: str, endpoint: str, json_data: Optional[Dict] = None) -> Dict:
        """Make an HTTP request to the Notion API."""
        url = f"{self.API_BASE}{endpoint}"
        response = httpx.request(
            method=method,
            url=url,
            headers=self.headers,
            json=json_data,
            timeout=30,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Notion API error ({response.status_code}): {response.text}")
        return response.json()

    def validate_database(self) -> bool:
        """Validate that the database exists and is accessible."""
        if not self.database_id:
            return False
        try:
            self._request("GET", f"/databases/{self.database_id}")
            self._database_validated = True
            return True
        except RuntimeError as e:
            print(f"Database validation failed: {e}")
            return False

    def create_database(self, parent_page_id: str) -> str:
        """
        Create a new database for fitness and diet logging.

        Args:
            parent_page_id: The ID of the parent page where the database will be created.

        Returns:
            The ID of the newly created database.
        """
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": settings.DATABASE_NAME}}],
            "properties": settings.DATABASE_PROPERTIES,
        }
        response = self._request("POST", "/databases", payload)
        self.database_id = response["id"]
        self._database_validated = True
        return self.database_id

    def create_log_entry(
        self,
        name: str,
        log_type: str,
        log_date: Optional[date] = None,
        description: Optional[str] = None,
        categories: Optional[List[str]] = None,
        calories: Optional[int] = None,
        protein: Optional[float] = None,
        duration: Optional[int] = None,
        weight: Optional[float] = None,
        mood_score: Optional[str] = None,
        energy_level: Optional[str] = None,
        image_url: Optional[str] = None,
        transcription: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new log entry in the Notion database.

        Args:
            name: Title of the log entry
            log_type: Type of log (Photo, Voice Note, Text Note, Meal, Workout, Weight, Mood)
            log_date: Date of the log entry (defaults to today)
            description: Description text
            categories: List of categories
            calories: Calorie count for meals
            protein: Protein in grams
            duration: Duration in minutes (for workouts)
            weight: Weight in pounds
            mood_score: Mood score (1-5)
            energy_level: Energy level (1-5)
            image_url: URL of uploaded image
            transcription: Voice note transcription
            tags: List of tags

        Returns:
            The created page object from Notion API.
        """
        if not self.database_id:
            raise ValueError("Database ID is required. Set NOTION_DATABASE_ID or create a database first.")

        log_date = log_date or date.today()

        # Build properties
        properties: Dict[str, Any] = {
            "Name": {"title": [{"text": {"content": name}}]},
            "Date": {"date": {"start": log_date.isoformat()}},
            "Type": {"select": {"name": log_type}},
        }

        if description:
            properties["Description"] = {
                "rich_text": [{"text": {"content": description[:2000]}}]
            }

        if categories:
            properties["Category"] = {
                "multi_select": [{"name": cat} for cat in categories]
            }

        if calories is not None:
            properties["Calories"] = {"number": calories}

        if protein is not None:
            properties["Protein (g)"] = {"number": protein}

        if duration is not None:
            properties["Duration (min)"] = {"number": duration}

        if weight is not None:
            properties["Weight (lbs)"] = {"number": weight}

        if mood_score:
            properties["Mood Score"] = {"select": {"name": mood_score}}

        if energy_level:
            properties["Energy Level"] = {"select": {"name": energy_level}}

        if image_url:
            properties["Image URL"] = {"url": image_url}

        if transcription:
            properties["Transcription"] = {
                "rich_text": [{"text": {"content": transcription[:2000]}}]
            }

        if tags:
            properties["Tags"] = {"multi_select": [{"name": tag} for tag in tags]}

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }

        return self._request("POST", "/pages", payload)

    def query_logs(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        log_type: Optional[str] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query log entries from the database.

        Args:
            start_date: Filter logs on or after this date
            end_date: Filter logs on or before this date
            log_type: Filter by log type
            categories: Filter by categories (any match)
            tags: Filter by tags (any match)
            limit: Maximum number of results

        Returns:
            List of matching log entries.
        """
        if not self.database_id:
            raise ValueError("Database ID is required.")

        filters = []

        if start_date:
            filters.append({
                "property": "Date",
                "date": {"on_or_after": start_date.isoformat()}
            })

        if end_date:
            filters.append({
                "property": "Date",
                "date": {"on_or_before": end_date.isoformat()}
            })

        if log_type:
            filters.append({
                "property": "Type",
                "select": {"equals": log_type}
            })

        if categories:
            for cat in categories:
                filters.append({
                    "property": "Category",
                    "multi_select": {"contains": cat}
                })

        if tags:
            for tag in tags:
                filters.append({
                    "property": "Tags",
                    "multi_select": {"contains": tag}
                })

        payload: Dict[str, Any] = {
            "page_size": min(limit, 100),
            "sorts": [{"property": "Date", "direction": "descending"}],
        }

        if filters:
            if len(filters) == 1:
                payload["filter"] = filters[0]
            else:
                payload["filter"] = {"and": filters}

        results = []
        has_more = True
        start_cursor = None

        while has_more and len(results) < limit:
            if start_cursor:
                payload["start_cursor"] = start_cursor

            response = self._request("POST", f"/databases/{self.database_id}/query", payload)
            results.extend(response.get("results", []))
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return results[:limit]

    def get_logs_for_date(self, target_date: date) -> List[Dict[str, Any]]:
        """Get all logs for a specific date."""
        return self.query_logs(start_date=target_date, end_date=target_date)

    def get_logs_for_week(self, week_start: date) -> List[Dict[str, Any]]:
        """Get all logs for a week starting from the given date."""
        from datetime import timedelta
        week_end = week_start + timedelta(days=6)
        return self.query_logs(start_date=week_start, end_date=week_end)

    def get_logs_for_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Get all logs for a specific month."""
        import calendar

        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        return self.query_logs(start_date=start_date, end_date=end_date)

    def update_log_entry(self, page_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing log entry.

        Args:
            page_id: The ID of the page to update
            **kwargs: Properties to update (same as create_log_entry)

        Returns:
            The updated page object.
        """
        properties = {}

        if "name" in kwargs:
            properties["Name"] = {"title": [{"text": {"content": kwargs["name"]}}]}

        if "log_date" in kwargs:
            properties["Date"] = {"date": {"start": kwargs["log_date"].isoformat()}}

        if "log_type" in kwargs:
            properties["Type"] = {"select": {"name": kwargs["log_type"]}}

        if "description" in kwargs:
            properties["Description"] = {
                "rich_text": [{"text": {"content": kwargs["description"][:2000]}}]
            }

        if "categories" in kwargs:
            properties["Category"] = {
                "multi_select": [{"name": cat} for cat in kwargs["categories"]]
            }

        if "calories" in kwargs:
            properties["Calories"] = {"number": kwargs["calories"]}

        if "protein" in kwargs:
            properties["Protein (g)"] = {"number": kwargs["protein"]}

        if "duration" in kwargs:
            properties["Duration (min)"] = {"number": kwargs["duration"]}

        if "weight" in kwargs:
            properties["Weight (lbs)"] = {"number": kwargs["weight"]}

        if "mood_score" in kwargs:
            properties["Mood Score"] = {"select": {"name": kwargs["mood_score"]}}

        if "energy_level" in kwargs:
            properties["Energy Level"] = {"select": {"name": kwargs["energy_level"]}}

        if "image_url" in kwargs:
            properties["Image URL"] = {"url": kwargs["image_url"]}

        if "transcription" in kwargs:
            properties["Transcription"] = {
                "rich_text": [{"text": {"content": kwargs["transcription"][:2000]}}]
            }

        if "tags" in kwargs:
            properties["Tags"] = {"multi_select": [{"name": tag} for tag in kwargs["tags"]]}

        return self._request("PATCH", f"/pages/{page_id}", {"properties": properties})

    def delete_log_entry(self, page_id: str) -> bool:
        """
        Archive (delete) a log entry.

        Args:
            page_id: The ID of the page to delete

        Returns:
            True if successful.
        """
        self._request("PATCH", f"/pages/{page_id}", {"archived": True})
        return True

    def extract_log_data(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from a Notion page object.

        Args:
            page: Raw Notion page object

        Returns:
            Dictionary with extracted field values.
        """
        props = page.get("properties", {})

        def get_title(prop):
            title = prop.get("title", [])
            return title[0]["text"]["content"] if title else ""

        def get_rich_text(prop):
            rt = prop.get("rich_text", [])
            return rt[0]["text"]["content"] if rt else ""

        def get_date(prop):
            d = prop.get("date")
            return d["start"] if d else None

        def get_select(prop):
            s = prop.get("select")
            return s["name"] if s else None

        def get_multi_select(prop):
            ms = prop.get("multi_select", [])
            return [item["name"] for item in ms]

        def get_number(prop):
            return prop.get("number")

        def get_url(prop):
            return prop.get("url")

        return {
            "id": page["id"],
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "name": get_title(props.get("Name", {})),
            "date": get_date(props.get("Date", {})),
            "type": get_select(props.get("Type", {})),
            "categories": get_multi_select(props.get("Category", {})),
            "description": get_rich_text(props.get("Description", {})),
            "calories": get_number(props.get("Calories", {})),
            "protein": get_number(props.get("Protein (g)", {})),
            "duration": get_number(props.get("Duration (min)", {})),
            "weight": get_number(props.get("Weight (lbs)", {})),
            "mood_score": get_select(props.get("Mood Score", {})),
            "energy_level": get_select(props.get("Energy Level", {})),
            "image_url": get_url(props.get("Image URL", {})),
            "transcription": get_rich_text(props.get("Transcription", {})),
            "tags": get_multi_select(props.get("Tags", {})),
        }
