import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { CalendarClock, Upload, Users, FileText, LogOut, Bell, Calendar } from "lucide-react";
import { format } from "date-fns";

export default function AdminDashboard({ user, onLogout }) {
  const [upcomingClasses, setUpcomingClasses] = useState([]);
  const [logs, setLogs] = useState([]);
  const [users, setUsers] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [newClass, setNewClass] = useState({
    title: "",
    room: "",
    teacher_email: "",
    start_datetime: "",
    end_datetime: "",
    recurrence: "ONCE"
  });

  useEffect(() => {
    fetchUpcoming();
    fetchLogs();
    fetchUsers();
  }, []);

  const fetchUpcoming = async () => {
    try {
      const response = await axios.get(`${API}/admin/upcoming?hours=48`);
      setUpcomingClasses(response.data);
    } catch (error) {
      toast.error("Failed to fetch upcoming classes");
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/admin/logs?limit=50`);
      setLogs(response.data);
    } catch (error) {
      toast.error("Failed to fetch logs");
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error("Failed to fetch users");
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API}/admin/timetables/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success(`${response.data.classes_created} classes uploaded successfully!`);
      fetchUpcoming();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Upload failed");
    }
    setUploading(false);
  };

  const handleCreateClass = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/admin/classes`, newClass);
      toast.success("Class created successfully!");
      setNewClass({
        title: "",
        room: "",
        teacher_email: "",
        start_datetime: "",
        end_datetime: "",
        recurrence: "ONCE"
      });
      fetchUpcoming();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create class");
    }
  };

  const sendTestReminder = async () => {
    try {
      await axios.post(`${API}/admin/test-reminder?user_email=${user.email}`);
      toast.success("Test reminder sent!");
    } catch (error) {
      toast.error("Failed to send test reminder");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CalendarClock className="w-8 h-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
              Admin Dashboard
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user.name}</span>
            <Button
              variant="outline"
              onClick={onLogout}
              data-testid="logout-button"
              className="flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="bg-white shadow-sm">
            <TabsTrigger value="overview" data-testid="overview-tab">Overview</TabsTrigger>
            <TabsTrigger value="upload" data-testid="upload-tab">Upload Timetable</TabsTrigger>
            <TabsTrigger value="create" data-testid="create-tab">Create Class</TabsTrigger>
            <TabsTrigger value="users" data-testid="users-tab">Users</TabsTrigger>
            <TabsTrigger value="logs" data-testid="logs-tab">Logs</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6" data-testid="overview-content">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="border-l-4 border-l-blue-600">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Calendar className="w-5 h-5 text-blue-600" />
                    Upcoming Classes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-gray-900">{upcomingClasses.length}</p>
                  <p className="text-sm text-gray-600">Next 48 hours</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-green-600">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Users className="w-5 h-5 text-green-600" />
                    Total Users
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-gray-900">{users.length}</p>
                  <p className="text-sm text-gray-600">Registered staff</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-purple-600">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Bell className="w-5 h-5 text-purple-600" />
                    Test Reminder
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={sendTestReminder}
                    data-testid="test-reminder-button"
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    Send to My Email
                  </Button>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Upcoming Classes (Next 48 Hours)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {upcomingClasses.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No upcoming classes</p>
                  ) : (
                    upcomingClasses.map((cls) => (
                      <div
                        key={cls.id}
                        className="p-4 bg-blue-50 rounded-lg border border-blue-200"
                        data-testid="class-card"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-semibold text-gray-900">{cls.title}</h3>
                            <p className="text-sm text-gray-600">Room: {cls.room}</p>
                            <p className="text-sm text-gray-600">Teacher: {cls.teacher_email}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-blue-600">
                              {format(new Date(cls.start_datetime), "MMM dd, yyyy")}
                            </p>
                            <p className="text-sm text-gray-600">
                              {format(new Date(cls.start_datetime), "hh:mm a")}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload" data-testid="upload-content">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-6 h-6" />
                  Upload Timetable
                </CardTitle>
                <CardDescription>
                  Upload a CSV or Excel file with columns: class_title, room, teacher_email, start_datetime, end_datetime, recurrence (optional)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <Label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-blue-600 hover:text-blue-700 font-medium">Choose a file</span>
                    <span className="text-gray-600"> or drag and drop</span>
                  </Label>
                  <Input
                    id="file-upload"
                    data-testid="file-upload-input"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="hidden"
                  />
                  <p className="text-xs text-gray-500 mt-2">CSV or Excel files only</p>
                </div>
                {uploading && <p className="text-center text-blue-600">Uploading...</p>}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Create Class Tab */}
          <TabsContent value="create" data-testid="create-content">
            <Card>
              <CardHeader>
                <CardTitle>Create New Class</CardTitle>
                <CardDescription>Manually add a single class to the timetable</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateClass} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="title">Class Title</Label>
                      <Input
                        id="title"
                        data-testid="class-title-input"
                        placeholder="Mathematics 101"
                        value={newClass.title}
                        onChange={(e) => setNewClass({ ...newClass, title: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="room">Room</Label>
                      <Input
                        id="room"
                        data-testid="class-room-input"
                        placeholder="Room 203"
                        value={newClass.room}
                        onChange={(e) => setNewClass({ ...newClass, room: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="teacher_email">Teacher Email</Label>
                      <Input
                        id="teacher_email"
                        data-testid="class-teacher-email-input"
                        type="email"
                        placeholder="teacher@school.com"
                        value={newClass.teacher_email}
                        onChange={(e) => setNewClass({ ...newClass, teacher_email: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="recurrence">Recurrence</Label>
                      <select
                        id="recurrence"
                        data-testid="class-recurrence-select"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        value={newClass.recurrence}
                        onChange={(e) => setNewClass({ ...newClass, recurrence: e.target.value })}
                      >
                        <option value="ONCE">Once</option>
                        <option value="WEEKLY">Weekly</option>
                        <option value="ODD_WEEKS">Odd Weeks</option>
                        <option value="EVEN_WEEKS">Even Weeks</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="start_datetime">Start Date & Time</Label>
                      <Input
                        id="start_datetime"
                        data-testid="class-start-input"
                        type="datetime-local"
                        value={newClass.start_datetime}
                        onChange={(e) => setNewClass({ ...newClass, start_datetime: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="end_datetime">End Date & Time</Label>
                      <Input
                        id="end_datetime"
                        data-testid="class-end-input"
                        type="datetime-local"
                        value={newClass.end_datetime}
                        onChange={(e) => setNewClass({ ...newClass, end_datetime: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <Button type="submit" data-testid="create-class-button" className="w-full bg-blue-600 hover:bg-blue-700">
                    Create Class
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" data-testid="users-content">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-6 h-6" />
                  Registered Users
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Email</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Phone</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Role</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {users.map((u) => (
                        <tr key={u.id} className="hover:bg-gray-50" data-testid="user-row">
                          <td className="px-4 py-3 text-sm text-gray-900">{u.name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{u.phone || "N/A"}</td>
                          <td className="px-4 py-3 text-sm">
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-medium ${
                                u.role === "admin" ? "bg-purple-100 text-purple-800" : "bg-blue-100 text-blue-800"
                              }`}
                            >
                              {u.role}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Logs Tab */}
          <TabsContent value="logs" data-testid="logs-content">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-6 h-6" />
                  Reminder Logs
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {logs.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No logs yet</p>
                  ) : (
                    logs.map((log) => (
                      <div
                        key={log.id}
                        className="p-3 border rounded-lg"
                        data-testid="log-entry"
                      >
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">{log.response}</span>
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              log.status === "sent" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                            }`}
                          >
                            {log.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {log.timestamp ? format(new Date(log.timestamp), "MMM dd, yyyy hh:mm a") : "N/A"}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
