# TimelyTeach - Timetable Reminder Web Application

A modern web application that helps teachers and staff remember their scheduled classes with automated reminders via email, SMS, and push notifications.

## Features

### User Roles
- **Admin**: Upload/manage timetables, manage staff, configure notifications
- **Staff**: View personal timetable, set reminder preferences

### Timetable Management
- Upload weekly timetables via CSV/Excel
- Manually create classes through UI form
- Support for recurring classes (Weekly, Odd Weeks, Even Weeks)
- Handle substitutions and cancellations

### Reminder System
- Automated reminders before classes (5-60 minutes configurable)
- Multiple channels: Email, SMS (Twilio), Push notifications
- Retry mechanism for failed reminders
- Quiet hours support
- Comprehensive logging

### Admin Dashboard
- View upcoming classes (24/48 hours)
- Monitor reminder delivery logs
- Manage all users
- Send test reminders
- Upload timetables

### Staff Dashboard
- View upcoming classes (7 days)
- Customize notification preferences
- Set reminder lead time
- Enable/disable notification channels
- Configure quiet hours

## Tech Stack

**Backend:**
- FastAPI (Python)
- MongoDB with Motor (async driver)
- JWT Authentication with bcrypt
- APScheduler (background job scheduler)
- SMTP for email notifications
- Pandas for CSV/Excel parsing

**Frontend:**
- React 19
- Shadcn/UI components
- Tailwind CSS
- Axios for API calls
- React Router for navigation
- Sonner for toast notifications

## Setup Instructions

### Email Configuration

To enable email reminders, configure SMTP settings in `/app/backend/.env`:

```env
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASS="your-app-password"
```

**Gmail Setup:**
1. Enable 2-Factor Authentication
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the app password in `SMTP_PASS`

### CSV Upload Format

Example `timetable.csv`:
```csv
class_title,room,teacher_email,start_datetime,end_datetime,recurrence
Mathematics 101,Room 203,john@school.com,2025-11-25T09:00:00,2025-11-25T10:30:00,WEEKLY
Physics Lab,Lab A,jane@school.com,2025-11-25T11:00:00,2025-11-25T13:00:00,WEEKLY
Chemistry 201,Room 305,bob@school.com,2025-11-26T14:00:00,2025-11-26T15:30:00,ONCE
```

## Usage Guide

### For Administrators

1. **Register**: Create an admin account by selecting "Administrator" role during registration
2. **Upload Timetable**: Use the "Upload Timetable" tab to upload CSV/Excel files
3. **Create Classes**: Manually add classes via the "Create Class" form
4. **Monitor**: View upcoming classes, logs, and user activity
5. **Test**: Send test reminders to verify email configuration

### For Staff/Teachers

1. **Register**: Create a staff account with your school email
2. **View Schedule**: See your upcoming classes for the next 7 days
3. **Set Preferences**: Customize reminder lead time (5-60 minutes)
4. **Configure Channels**: Enable/disable email, SMS, push notifications
5. **Quiet Hours**: Set times when you don't want to receive notifications

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Admin Routes
- `POST /api/admin/timetables/upload` - Upload timetable file
- `POST /api/admin/classes` - Create single class
- `GET /api/admin/upcoming?hours=24` - Get upcoming classes
- `GET /api/admin/logs?limit=100` - Get reminder logs
- `POST /api/admin/test-reminder?user_email=` - Send test reminder
- `GET /api/admin/users` - Get all users

### Staff Routes
- `GET /api/users/me/timetable` - Get my full timetable
- `GET /api/users/me/classes?days=7` - Get upcoming classes
- `PUT /api/users/me/preferences` - Update notification preferences

### System
- `GET /api/health` - Health check

## Scheduler

The application uses APScheduler to check for pending reminders every 5 minutes:
1. Fetches reminders scheduled for the current time
2. Sends notifications via configured channels
3. Updates reminder status and logs results
4. Handles retry logic for failed deliveries

## Database Collections

- **users**: User accounts with roles and preferences
- **classes**: Scheduled classes with recurrence rules
- **reminders**: Pending and sent reminders
- **logs**: Notification delivery logs

## Security
- JWT authentication with 7-day expiry
- Bcrypt password hashing
- Role-based access control
- Secure token storage

## Future Enhancements
- SMS via Twilio
- Push notifications
- WhatsApp integration
- Google Calendar sync
- ICS export
- Mobile app
