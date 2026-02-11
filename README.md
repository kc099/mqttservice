# MQTT Client for AWS Lightsail

A Python-based MQTT client service that runs on AWS Lightsail, connecting to an MQTT broker, receiving data from multiple device types, storing it in SQLite, and responding to data requests from mobile applications.

## Features

- **Three Device Types Support**:
  - Temperature devices (temperature & humidity with timestamps)
  - Power status devices (power toggle status)
  - Fingerprint sensors (authentication with pass/fail status)

- **SQLite Database Storage**: Local disk storage for all device data with date-based indexing
- **Request-Response Pattern**: Mobile apps can request data via MQTT topics
- **Per-Client Topics**: Unique topics for each client to prevent data conflicts
- **Date-based Data Retrieval**: Restricts data to one date per request to minimize MQTT traffic
- **Logging**: Comprehensive logging to file and console

## Project Structure

```
mqtt-client/
├── database.py              # Database creation and helper functions
├── config.py               # Configuration settings
├── mqtt_client.py          # Main MQTT client implementation
├── requirements.txt        # Python dependencies
├── mqtt-client.service     # Systemd service file
├── mqtt_data.db            # SQLite database (auto-created)
├── mqtt_client.log         # Log file (auto-created)
└── README.md              # This file
```

## Database Schema

### temperature_logs
- `id`: Primary key
- `device_id`: Device identifier
- `temperature`: Temperature value (°C)
- `humidity`: Humidity percentage
- `status`: Temperature status (HIGH/LOW)
- `timestamp`: ISO format timestamp
- `date`: Date (YYYY-MM-DD) for easy querying
- `created_at`: Record creation timestamp

### power_status_logs
- `id`: Primary key
- `device_id`: Device identifier
- `ebstatus`: EB power status (ON/OFF or empty)
- `dgstatus`: DG power status (ON/OFF or empty)
- `timestamp`: ISO format timestamp
- `date`: Date (YYYY-MM-DD)
- `created_at`: Record creation timestamp

### fingerprint_logs
- `id`: Primary key
- `device_id`: Device identifier
- `user_id`: User identifier
- `auth_status`: Authentication status (PASS/FAIL)
- `timestamp`: ISO format timestamp
- `date`: Date (YYYY-MM-DD)
- `created_at`: Record creation timestamp

## Installation on AWS Lightsail

### Prerequisites
- Ubuntu 20.04 or later on AWS Lightsail
- Python 3.7 or higher
- SSH access to your Lightsail instance

### Setup Steps

1. **Connect to your Lightsail instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-lightsail-ip
   ```

2. **Update system packages**:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade -y
   ```

3. **Install Python and pip**:
   ```bash
   sudo apt-get install -y python3 python3-pip
   ```

4. **Create working directory**:
   ```bash
   mkdir -p /home/ubuntu/mqtt-client
   cd /home/ubuntu/mqtt-client
   ```

5. **Copy project files** to `/home/ubuntu/mqtt-client/`

6. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

7. **Set up systemd service**:
   ```bash
   sudo cp mqtt-client.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable mqtt-client.service
   ```

8. **Configure environment variables** (edit the service file):
   ```bash
   sudo nano /etc/systemd/system/mqtt-client.service
   ```

   Uncomment and update the Environment variables section with your MQTT broker details:
   ```
   Environment="MQTT_BROKER_HOST=your-mqtt-broker.com"
   Environment="MQTT_BROKER_PORT=1883"
   Environment="MQTT_CLIENT_ID=mqtt_client_1"
   Environment="MQTT_USERNAME=your_username"
   Environment="MQTT_PASSWORD=your_password"
   ```

9. **Start the service**:
   ```bash
   sudo systemctl start mqtt-client.service
   ```

10. **Verify service is running**:
    ```bash
    sudo systemctl status mqtt-client.service
    ```

## Configuration

Edit `config.py` to customize settings:

- `MQTT_BROKER_HOST`: MQTT broker address (default: localhost)
- `MQTT_BROKER_PORT`: MQTT broker port (default: 1883)
- `MQTT_CLIENT_ID`: Unique client identifier
- `MQTT_USERNAME`: MQTT broker username (optional)
- `MQTT_PASSWORD`: MQTT broker password (optional)

### Topic Configuration

- **Temperature Receive**: `home/temperature`
- **Power Receive**: `home/power`
- **Fingerprint Receive**: `home/fingerprint`
- **Temperature Request**: `home/gettemp/{client_id}`
- **Temperature Response**: `home/datatemp/{client_id}`
- **Power Request**: `home/getpower/{client_id}`
- **Power Response**: `home/datapower/{client_id}`
- **Fingerprint Request**: `home/getfingerprint/{client_id}`
- **Fingerprint Response**: `home/datafingerprint/{client_id}`

## Message Format

### Temperature Device Message (from device)
```json
{
  "device_id": "temp_sensor_01",
  "temperature": 22.5,
  "humidity": 45.3,
  "status": "HIGH",
  "timestamp": "2026-01-22T14:30:00"
}
```
> `status` is `HIGH` or `LOW` — stored in DB but can be ignored for display.

### Power Status Device Message (from device)
```json
{
  "device_id": "power_switch_01",
  "status": "EB_ON",
  "timestamp": "2026-01-22T14:35:15"
}
```
> `status` is one of: `DG_ON`, `DG_OFF`, `EB_ON`, `EB_OFF`.  
> The client parses this into separate `ebstatus` / `dgstatus` columns (ON/OFF) in the database.

### Fingerprint Sensor Message (from device)
```json
{
  "device_id": "fingerprint_01",
  "user_id": "user_123",
  "authStatus": "PASS",
  "timestamp": "2026-01-22T14:40:22"
}
```
> Note: the device sends `authStatus` (camelCase). Stored as `auth_status` in the database.

### Temperature Data Request (from Mobile App)
```json
{
  "device_id": "temp_sensor_01",
  "date": "2026-01-22"
}
```

### Temperature Data Response
```json
{
  "device_id": "temp_sensor_01",
  "date": "2026-01-22",
  "count": 48,
  "records": [
    {
      "temperature": 22.5,
      "humidity": 45.3,
      "status": "HIGH",
      "timestamp": "2026-01-22T14:30:00"
    },
    ...
  ]
}
```

### Power Status Data Request (from Mobile App)
```json
{
  "device_id": "power_switch_01",
  "date": "2026-01-22"
}
```

### Power Status Data Response
```json
{
  "device_id": "power_switch_01",
  "date": "2026-01-22",
  "count": 3,
  "records": [
    {
      "ebstatus": "ON",
      "dgstatus": "OFF",
      "timestamp": "2026-01-22T09:15:00"
    }
  ]
}
```

### Fingerprint Data Request (from Mobile App)
```json
{
  "device_id": "fingerprint_01",
  "date": "2026-01-22"
}
```

### Fingerprint Data Response
```json
{
  "device_id": "fingerprint_01",
  "date": "2026-01-22",
  "count": 5,
  "records": [
    {
      "user_id": "user_123",
      "authStatus": "PASS",
      "timestamp": "2026-01-22T14:40:22"
    }
  ]
}
```

## Viewing Logs

View real-time logs:
```bash
sudo journalctl -u mqtt-client.service -f
```

View log file:
```bash
tail -f /home/ubuntu/mqtt-client/mqtt_client.log
```

## Querying the Database

Connect to SQLite database:
```bash
sqlite3 /home/ubuntu/mqtt-client/mqtt_data.db
```

Example queries:
```sql
-- View temperature data for a specific date
SELECT * FROM temperature_logs WHERE date = '2026-01-22' ORDER BY timestamp DESC;

-- View power status changes
SELECT * FROM power_status_logs ORDER BY timestamp DESC LIMIT 10;

-- View fingerprint authentication logs
SELECT * FROM fingerprint_logs WHERE date = '2026-01-22' ORDER BY timestamp DESC;

-- Count records by device
SELECT device_id, COUNT(*) as count FROM temperature_logs GROUP BY device_id;
```

## Troubleshooting

### Service fails to start
- Check service status: `sudo systemctl status mqtt-client.service`
- View logs: `sudo journalctl -u mqtt-client.service -n 50`
- Verify MQTT broker is reachable from Lightsail instance

### Connection timeout
- Ensure MQTT broker address and port are correct
- Check security groups allow outbound connection on MQTT port
- Verify firewall rules on the MQTT broker

### Database errors
- Check file permissions: `ls -la /home/ubuntu/mqtt-client/`
- Ensure ubuntu user has write permissions: `sudo chown -R ubuntu:ubuntu /home/ubuntu/mqtt-client/`

### High CPU usage
- Check for excessive logging by adjusting `LOG_LEVEL` to WARNING
- Monitor database size and consider archiving old data

## Performance Optimization

1. **Database Maintenance**: Periodically archive old data
2. **Log Rotation**: Set up logrotate for `mqtt_client.log`
3. **Index Optimization**: Pre-created indexes on device_id and date
4. **Connection Pooling**: Handled internally by database module

## Security Considerations

- Use MQTT username and password for broker authentication
- Configure AWS security groups to restrict access
- Ensure SSL/TLS encryption if available from MQTT broker
- Regularly backup SQLite database
- Restrict file permissions on the service directory

## Manual Testing

Run the client manually for testing:
```bash
python3 mqtt_client.py
```

Press Ctrl+C to stop.

## Support

For issues or questions, check:
1. Service logs
2. MQTT broker connectivity
3. Message format compliance
4. Database permissions
