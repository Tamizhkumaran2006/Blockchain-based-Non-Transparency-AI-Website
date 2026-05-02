import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Shield, Sparkles, Lock, Mail, User, KeyRound } from "lucide-react";
import { toast } from "sonner";

export const Route = createFileRoute("/auth")({
  component: AuthPage,
});

function AuthPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  // Handle Google OAuth callback
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');
      const user = urlParams.get('user');
      
      if (token && user) {
        setIsLoading(true);
        localStorage.setItem("token", token);
        
        // Fetch user details
        fetch("http://localhost:5000/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` }
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              localStorage.setItem("user", JSON.stringify(data.user));
              toast.success("Google login successful!");
              navigate({ to: "/dashboard" });
            } else {
              toast.error("Failed to fetch user details");
              setIsLoading(false);
            }
          })
          .catch(err => {
            console.error("Failed to fetch user:", err);
            toast.error("Failed to complete login");
            setIsLoading(false);
          });
      }
    }
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      const response = await fetch("http://localhost:5000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
        toast.success("Login successful!");
        navigate({ to: "/dashboard" });
      } else {
        toast.error(data.detail || "Login failed");
      }
    } catch (error) {
      toast.error("Connection error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const name = formData.get("name") as string;
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const role = formData.get("role") as string;

    try {
      const response = await fetch("http://localhost:5000/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, role }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
        toast.success("Registration successful!");
        navigate({ to: "/dashboard" });
      } else {
        toast.error(data.detail || "Registration failed");
      }
    } catch (error) {
      toast.error("Connection error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    // Initialize Google One-Tap
    if (typeof window !== 'undefined' && (window as any).google) {
      try {
        const google = (window as any).google;
        google.accounts.id.initialize({
          client_id: "608687632539-2o6insdcvhdb2i1bvq6k6mcqart8rfq3.apps.googleusercontent.com",
          callback: async (response: any) => {
            setIsLoading(true);
            try {
              const res = await fetch("http://localhost:5000/api/auth/google", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                  id_token: response.credential,
                  role: "client" 
                }),
              });

              const data = await res.json();

              if (res.ok) {
                localStorage.setItem("token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
                toast.success("Google login successful!");
                navigate({ to: "/dashboard" });
              } else {
                toast.error(data.detail || "Google login failed");
              }
            } catch (error) {
              toast.error("Connection error. Please try again.");
            } finally {
              setIsLoading(false);
            }
          },
        });
        google.accounts.id.prompt();
      } catch (error) {
        toast.error("Google Sign-In not available. Please use email/password.");
      }
    } else {
      toast.error("Google Sign-In not loaded. Please refresh and try again.");
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4 relative overflow-hidden">
      {/* Sophisticated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0a0a0a_1px,transparent_1px),linear-gradient(to_bottom,#0a0a0a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)]"></div>
        <div className="absolute top-20 left-20 w-96 h-96 bg-blue-600/5 rounded-full blur-[120px] animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-cyan-600/5 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      {/* Loading State for Google OAuth */}
      {isLoading && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block h-16 w-16 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent mb-4"></div>
            <p className="text-white text-xl font-semibold">Completing Google Sign In...</p>
            <p className="text-gray-400 text-sm mt-2">Please wait</p>
          </div>
        </div>
      )}

      <div className="w-full max-w-md relative z-10">
        {/* Logo Section */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center gap-3 mb-6 group">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl blur-lg opacity-50 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative bg-gradient-to-br from-blue-600 to-cyan-600 p-3 rounded-xl">
                <Shield className="h-8 w-8 text-white" />
              </div>
            </div>
            <div>
              <span className="text-3xl font-bold bg-gradient-to-r from-white via-blue-100 to-cyan-100 bg-clip-text text-transparent">
                Verity AI
              </span>
              <p className="text-xs text-gray-600 -mt-1 tracking-wider uppercase">Secure Lending Platform</p>
            </div>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600/10 backdrop-blur-xl border border-blue-500/20 text-blue-300 rounded-full text-sm font-medium">
            <Sparkles className="h-4 w-4" />
            <span>Welcome back! Sign in to continue</span>
          </div>
        </div>

        {/* Auth Card */}
        <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-2xl shadow-blue-600/10">
          <CardHeader className="space-y-1 pb-6 border-b border-gray-800">
            <CardTitle className="text-2xl font-bold text-white">Account Access</CardTitle>
            <CardDescription className="text-gray-400">Login or create an account to continue</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <Tabs defaultValue="login">
              <TabsList className="grid w-full grid-cols-2 mb-6 bg-gray-900/50 p-1 border border-gray-800">
                <TabsTrigger 
                  value="login" 
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-cyan-600 data-[state=active]:text-white text-gray-400"
                >
                  Login
                </TabsTrigger>
                <TabsTrigger 
                  value="register"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-cyan-600 data-[state=active]:text-white text-gray-400"
                >
                  Register
                </TabsTrigger>
              </TabsList>

              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-5">
                  <div>
                    <Label htmlFor="login-email" className="text-gray-300 font-medium">Email Address</Label>
                    <div className="relative mt-2">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        id="login-email"
                        name="email"
                        type="email"
                        placeholder="your@email.com"
                        required
                        className="pl-10 bg-gray-900/50 border-gray-800 text-white placeholder:text-gray-600 focus:border-blue-600 focus:ring-2 focus:ring-blue-600/50"
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="login-password" className="text-gray-300 font-medium">Password</Label>
                    <div className="relative mt-2">
                      <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        id="login-password"
                        name="password"
                        type="password"
                        placeholder="••••••••"
                        required
                        className="pl-10 bg-gray-900/50 border-gray-800 text-white placeholder:text-gray-600 focus:border-blue-600 focus:ring-2 focus:ring-blue-600/50"
                      />
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-gradient-to-r from-blue-600 via-cyan-600 to-purple-600 hover:from-blue-700 hover:via-cyan-700 hover:to-purple-700 text-white shadow-lg shadow-blue-500/50 hover:shadow-xl hover:shadow-blue-500/70 transition-all duration-300 hover:scale-105" 
                    disabled={isLoading}
                  >
                    {isLoading ? "Logging in..." : "Login to Dashboard"}
                  </Button>
                </form>

                <div className="mt-6">
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-gray-800" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-black px-2 text-gray-500">Or continue with</span>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full mt-4 bg-gray-900/50 border-gray-800 text-white hover:bg-gray-800 hover:border-gray-700 transition-all duration-300"
                    onClick={handleGoogleLogin}
                  >
                    <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
                      <path
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                        fill="#4285F4"
                      />
                      <path
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        fill="#34A853"
                      />
                      <path
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                        fill="#FBBC05"
                      />
                      <path
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        fill="#EA4335"
                      />
                    </svg>
                    Continue with Google
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="register">
                <form onSubmit={handleRegister} className="space-y-5">
                  <div>
                    <Label htmlFor="register-name" className="text-gray-300 font-medium">Full Name</Label>
                    <div className="relative mt-2">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        id="register-name"
                        name="name"
                        type="text"
                        placeholder="John Doe"
                        required
                        className="pl-10 bg-gray-900/50 border-gray-800 text-white placeholder:text-gray-600 focus:border-blue-600 focus:ring-2 focus:ring-blue-600/50"
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="register-email" className="text-gray-300 font-medium">Email Address</Label>
                    <div className="relative mt-2">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        id="register-email"
                        name="email"
                        type="email"
                        placeholder="your@email.com"
                        required
                        className="pl-10 bg-gray-900/50 border-gray-800 text-white placeholder:text-gray-600 focus:border-blue-600 focus:ring-2 focus:ring-blue-600/50"
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="register-password" className="text-gray-300 font-medium">Password</Label>
                    <div className="relative mt-2">
                      <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        id="register-password"
                        name="password"
                        type="password"
                        placeholder="••••••••"
                        required
                        minLength={6}
                        className="pl-10 bg-gray-900/50 border-gray-800 text-white placeholder:text-gray-600 focus:border-blue-600 focus:ring-2 focus:ring-blue-600/50"
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1.5">Minimum 6 characters</p>
                  </div>
                  <div>
                    <Label htmlFor="register-role" className="text-gray-300 font-medium">I am a</Label>
                    <select
                      id="register-role"
                      name="role"
                      className="flex h-10 w-full rounded-md border bg-gray-900/50 border-gray-800 text-white px-3 py-2 text-sm mt-2 focus:border-blue-600 focus:ring-2 focus:ring-blue-600/50"
                      required
                    >
                      <option value="client">Loan Applicant</option>
                      <option value="manager">Manager / Approver</option>
                    </select>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-gradient-to-r from-blue-600 via-cyan-600 to-purple-600 hover:from-blue-700 hover:via-cyan-700 hover:to-purple-700 text-white shadow-lg shadow-blue-500/50 hover:shadow-xl hover:shadow-blue-500/70 transition-all duration-300 hover:scale-105" 
                    disabled={isLoading}
                  >
                    {isLoading ? "Creating account..." : "Create Account"}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-gray-500 mt-6">
          By continuing, you agree to our{" "}
          <a href="#" className="text-blue-400 hover:text-cyan-400 hover:underline transition-colors">Terms</a>
          {" "}and{" "}
          <a href="#" className="text-blue-400 hover:text-cyan-400 hover:underline transition-colors">Privacy Policy</a>
        </p>
      </div>
    </div>
  );
}
