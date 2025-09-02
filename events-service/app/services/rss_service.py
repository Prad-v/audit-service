"""
RSS Feed Generation Service

This module provides functionality to generate RSS feeds from incident data
for public status pages and external integrations.
"""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.schemas import Incident as IncidentDB, IncidentUpdate as IncidentUpdateDB
from app.models.events import IncidentStatus


async def generate_rss_feed(incidents: List[IncidentDB], db: AsyncSession) -> str:
    """Generate RSS feed XML from incident data"""
    
    # RSS feed header
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Product Status - Incident Updates</title>
    <description>Real-time updates on product outages and incidents</description>
    <link>https://status.example.com</link>
    <language>en-US</language>
    <lastBuildDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
    <ttl>300</ttl>
    <atom:link href="https://status.example.com/rss/feed" rel="self" type="application/rss+xml" />
"""
    
    # Add incidents as RSS items
    for incident in incidents:
        # Use the current incident status (which should be the most recent)
        title = f"{incident.title} - {incident.status.value.title()}"
        description = incident.public_message
        pub_date = incident.updated_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Create RSS item
        rss_content += f"""
    <item>
      <title>{escape_xml(title)}</title>
      <description>{escape_xml(description)}</description>
      <link>https://status.example.com/incidents/{incident.incident_id}</link>
      <guid>https://status.example.com/incidents/{incident.incident_id}</guid>
      <pubDate>{pub_date}</pubDate>
      <category>{incident.incident_type.value}</category>
      <severity>{incident.severity.value}</severity>
      <status>{incident.status.value}</status>
    </item>"""
    
    # Close RSS feed
    rss_content += """
  </channel>
</rss>"""
    
    return rss_content


def escape_xml(text: str) -> str:
    """Escape XML special characters"""
    if not text:
        return ""
    
    return text.replace("&", "&amp;") \
               .replace("<", "&lt;") \
               .replace(">", "&gt;") \
               .replace('"', "&quot;") \
               .replace("'", "&apos;")


async def generate_incident_rss_feed(incident: IncidentDB, updates: List[IncidentUpdateDB]) -> str:
    """Generate RSS feed for a specific incident with all updates"""
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Incident Updates - {escape_xml(incident.title)}</title>
    <description>Updates for incident: {escape_xml(incident.description)}</description>
    <link>https://status.example.com/incidents/{incident.incident_id}</link>
    <language>en-US</language>
    <lastBuildDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
    <ttl>300</ttl>
    <atom:link href="https://status.example.com/incidents/{incident.incident_id}/rss" rel="self" type="application/rss+xml" />
"""
    
    # Add updates as RSS items
    for update in updates:
        title = f"Status Update: {update.status.value.title()}"
        description = update.public_message
        pub_date = update.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        rss_content += f"""
    <item>
      <title>{escape_xml(title)}</title>
      <description>{escape_xml(description)}</description>
      <link>https://status.example.com/incidents/{incident.incident_id}#update-{update.update_id}</link>
      <guid>https://status.example.com/incidents/{incident.incident_id}#update-{update.update_id}</guid>
      <pubDate>{pub_date}</pubDate>
      <category>incident-update</category>
      <status>{update.status.value}</status>
      <updateType>{update.update_type}</updateType>
    </item>"""
    
    rss_content += """
  </channel>
</rss>"""
    
    return rss_content


async def generate_status_page_rss(incidents: List[IncidentDB], db: AsyncSession) -> str:
    """Generate comprehensive status page RSS feed"""
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Product Status Page</title>
    <description>Complete status of all services and incidents</description>
    <link>https://status.example.com</link>
    <language>en-US</language>
    <lastBuildDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
    <ttl>60</ttl>
    <atom:link href="https://status.example.com/rss/status" rel="self" type="application/rss+xml" />
"""
    
    # Group incidents by status
    active_incidents = [i for i in incidents if i.status != IncidentStatus.RESOLVED]
    resolved_incidents = [i for i in incidents if i.status == IncidentStatus.RESOLVED]
    
    # Add active incidents first
    for incident in active_incidents:
        latest_update_query = select(IncidentUpdateDB).where(
            IncidentUpdateDB.incident_id == incident.incident_id
        ).order_by(IncidentUpdateDB.created_at.desc())
        
        latest_update_result = await db.execute(latest_update_query)
        latest_update = latest_update_result.scalar_one_or_none()
        
        if latest_update:
            title = f"🚨 {incident.title} - {incident.status.value.title()}"
            description = f"Severity: {incident.severity.value} | {latest_update.public_message}"
            pub_date = latest_update.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            rss_content += f"""
    <item>
      <title>{escape_xml(title)}</title>
      <description>{escape_xml(description)}</description>
      <link>https://status.example.com/incidents/{incident.incident_id}</link>
      <guid>https://status.example.com/incidents/{incident.incident_id}</guid>
      <pubDate>{pub_date}</pubDate>
      <category>active-incident</category>
      <severity>{incident.severity.value}</severity>
      <status>{incident.status.value}</status>
    </item>"""
    
    # Add resolved incidents
    for incident in resolved_incidents:
        latest_update_query = select(IncidentUpdateDB).where(
            IncidentUpdateDB.incident_id == incident.incident_id
        ).order_by(IncidentUpdateDB.created_at.desc())
        
        latest_update_result = await db.execute(latest_update_query)
        latest_update = latest_update_result.scalar_one_or_none()
        
        if latest_update:
            title = f"✅ {incident.title} - Resolved"
            description = f"Resolved at {incident.end_time.strftime('%Y-%m-%d %H:%M UTC') if incident.end_time else 'Unknown'}"
            pub_date = latest_update.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            rss_content += f"""
    <item>
      <title>{escape_xml(title)}</title>
      <description>{escape_xml(description)}</description>
      <link>https://status.example.com/incidents/{incident.incident_id}</link>
      <guid>https://status.example.com/incidents/{incident.incident_id}</guid>
      <pubDate>{pub_date}</pubDate>
      <category>resolved-incident</category>
      <severity>{incident.severity.value}</severity>
      <status>{incident.status.value}</status>
    </item>"""
    
    rss_content += """
  </channel>
</rss>"""
    
    return rss_content
