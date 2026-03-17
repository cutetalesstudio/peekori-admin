'use client';  // Mark the component as a Client Component

import { useEffect, useState } from 'react';

interface User {
  email: string;
  user_id: string;
}

const LandingPage = () => {
   const [user, setUser] = useState<User | null>(null);

  
  useEffect(() => {
  const fetchUser = async () => {
    await new Promise(r => setTimeout(r, 200));
    
    const response = await fetch('/api/auth/me', {
      credentials: 'include'
    });

    if (response.ok) {
      const data = await response.json();
      setUser(data);
    }
  };

  fetchUser();
}, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <h1 className="text-4xl font-semibold text-black dark:text-zinc-50">
      Welcome to the Landing Page!
      </h1>
      {user ? (
        <div>
          <p>Welcome, {user.email}</p>  {/* TypeScript knows 'user.email' is valid now */}
          <p>User ID: {user.user_id}</p> {/* TypeScript knows 'user.user_id' is valid now */}
        </div>
      ) : (
        <p>Loading...</p>
      )}
      </main>
    </div>
  );
};

export default LandingPage;
