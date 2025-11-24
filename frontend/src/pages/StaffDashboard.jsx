import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { CalendarClock, LogOut, Settings, Calendar, Bell } from "lucide-react";
import { format } from "date-fns";

export default function StaffDashboard({ user, onLogout }) {
  const [classes, setClasses] = useState([]);
  const [preferences, setPreferences] = useState(user.preferences || {
    lead_time_minutes: 15,
    channels: { email: true, sms: false, push: false },
    quiet_hours: { enabled: false, start: "22:00", end: "07:00" }
  });

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const response = await axios.get(`${API}/users/me/classes?days=7`);
      setClasses(response.data);
    } catch (error) {
      toast.error("Failed to fetch classes");
    }
  };

  const updatePreferences = async (newPrefs) => {
    try {
      await axios.put(`${API}/users/me/preferences`, newPrefs);
      setPreferences({ ...preferences, ...newPrefs });
      toast.success("Preferences updated!");
    } catch (error) {
      toast.error("Failed to update preferences");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CalendarClock className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
                My Schedule
              </h1>
              <p className="text-sm text-gray-600">Welcome, {user.name}</p>
            </div>
          </div>
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
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Classes */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-6 h-6 text-blue-600" />
                  Upcoming Classes (Next 7 Days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {classes.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No upcoming classes</p>
                  ) : (
                    classes.map((cls) => (
                      <div
                        key={cls.id}
                        className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
                        data-testid="class-card"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg text-gray-900">{cls.title}</h3>
                            <div className="mt-2 space-y-1">
                              <p className="text-sm text-gray-600 flex items-center gap-2">
                                <span className="font-medium">Room:</span> {cls.room}
                              </p>
                              <p className="text-sm text-gray-600 flex items-center gap-2">
                                <span className="font-medium">Date:</span> {format(new Date(cls.start_datetime), "EEEE, MMM dd, yyyy")}
                              </p>
                              <p className="text-sm text-gray-600 flex items-center gap-2">
                                <span className="font-medium">Time:</span> {format(new Date(cls.start_datetime), "hh:mm a")} - {format(new Date(cls.end_datetime), "hh:mm a")}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded-full">
                              {cls.recurrence}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right: Preferences */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5 text-blue-600" />
                  Reminder Settings
                </CardTitle>
                <CardDescription>Customize your notification preferences</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-3">
                  <Label>Remind me before class</Label>
                  <select
                    data-testid="lead-time-select"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    value={preferences.lead_time_minutes}
                    onChange={(e) => updatePreferences({ lead_time_minutes: parseInt(e.target.value) })}
                  >
                    <option value="5">5 minutes</option>
                    <option value="10">10 minutes</option>
                    <option value="15">15 minutes</option>
                    <option value="30">30 minutes</option>
                    <option value="60">1 hour</option>
                  </select>
                </div>

                <div className="space-y-4">
                  <Label>Notification Channels</Label>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Bell className="w-4 h-4 text-blue-600" />
                        <span className="text-sm">Email</span>
                      </div>
                      <Switch
                        data-testid="email-switch"
                        checked={preferences.channels.email}
                        onCheckedChange={(checked) =>
                          updatePreferences({ channels: { ...preferences.channels, email: checked } })
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between opacity-50">
                      <div className="flex items-center gap-2">
                        <Bell className="w-4 h-4 text-gray-400" />
                        <span className="text-sm">SMS</span>
                        <span className="text-xs text-gray-400">(Coming soon)</span>
                      </div>
                      <Switch disabled />
                    </div>
                    <div className="flex items-center justify-between opacity-50">
                      <div className="flex items-center gap-2">
                        <Bell className="w-4 h-4 text-gray-400" />
                        <span className="text-sm">Push Notification</span>
                        <span className="text-xs text-gray-400">(Coming soon)</span>
                      </div>
                      <Switch disabled />
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between mb-3">
                    <Label>Quiet Hours</Label>
                    <Switch
                      data-testid="quiet-hours-switch"
                      checked={preferences.quiet_hours.enabled}
                      onCheckedChange={(checked) =>
                        updatePreferences({ quiet_hours: { ...preferences.quiet_hours, enabled: checked } })
                      }
                    />
                  </div>
                  {preferences.quiet_hours.enabled && (
                    <div className="space-y-2">
                      <div>
                        <Label className="text-xs">Start</Label>
                        <input
                          type="time"
                          data-testid="quiet-start-input"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                          value={preferences.quiet_hours.start}
                          onChange={(e) =>
                            updatePreferences({ quiet_hours: { ...preferences.quiet_hours, start: e.target.value } })
                          }
                        />
                      </div>
                      <div>
                        <Label className="text-xs">End</Label>
                        <input
                          type="time"
                          data-testid="quiet-end-input"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                          value={preferences.quiet_hours.end}
                          onChange={(e) =>
                            updatePreferences({ quiet_hours: { ...preferences.quiet_hours, end: e.target.value } })
                          }
                        />
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200">
              <CardHeader>
                <CardTitle className="text-lg">Quick Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Classes this week</span>
                    <span className="text-2xl font-bold text-blue-600">{classes.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Reminder lead time</span>
                    <span className="text-lg font-semibold text-gray-900">{preferences.lead_time_minutes} min</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
