-- Clean up duplicate outage entries from the database
-- This script removes duplicate entries based on title, provider, and service

-- First, let's see what duplicates we have
WITH duplicates AS (
  SELECT 
    title,
    cloud_provider,
    service_name,
    COUNT(*) as count,
    MIN(event_time) as oldest_time,
    MAX(event_time) as newest_time
  FROM cloud_events 
  WHERE event_type = 'outage_status'
  GROUP BY title, cloud_provider, service_name
  HAVING COUNT(*) > 1
)
SELECT 
  title,
  cloud_provider,
  service_name,
  count as duplicate_count,
  oldest_time,
  newest_time
FROM duplicates
ORDER BY count DESC;

-- Now delete the duplicates, keeping only the most recent one
DELETE FROM cloud_events 
WHERE event_id IN (
  SELECT event_id FROM (
    SELECT 
      event_id,
      ROW_NUMBER() OVER (
        PARTITION BY title, cloud_provider, service_name 
        ORDER BY event_time DESC
      ) as rn
    FROM cloud_events 
    WHERE event_type = 'outage_status'
  ) ranked
  WHERE rn > 1
);

-- Verify the cleanup
SELECT 
  COUNT(*) as remaining_outages
FROM cloud_events 
WHERE event_type = 'outage_status';
