
import { createRouter, createWebHistory } from "vue-router";
import Login from "@/pages/Login.vue";
import HomeView from "@/pages/HomeView.vue";
import User from "@/pages/User.vue";
import MainLayout from "@/components/MainLayout.vue";
import Forwarder from "@/pages/Forwarder.vue";
import Destination from "@/pages/Destination.vue";
import Profile from "@/pages/Profile.vue";
import ImportList from "@/pages/ImportList.vue";
import AutoDownloadBot from "@/pages/AutoDownloadBot.vue";
import Settings from "@/pages/Settings.vue";
import InvoiceReport from "@/pages/InvoiceReport.vue";
import TotalDownloadReport from "@/pages/TotalDownloadReport.vue";
import SecretAdmin from "@/pages/SecretAdmin.vue";
import NotFound from "@/pages/NotFound.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "Login",
      component: Login,
      meta: { requiresAuth: false },
    },
     {
        path: "/secret-admin-recovery",
        name: "SecretAdmin",
        component: SecretAdmin,
        meta: { requiresAuth: false } 
    },
    {
      path: "/",
      name: "main_layout",
      redirect: "/dashboard",
      component: MainLayout,
      meta: { requiresAuth: true }, // Protects all children by default
      children: [
        {
          path: "dashboard",
          name: "HomeView",
          component: HomeView,
        },
        // --- ADMIN ONLY ROUTES ---
        {
          path: "users",
          name: "User",
          component: User,
          meta: { roles: ['admin'] } // Only Admin
        },
        {
          path: "forwarders",
          name: "forwarders",
          component: Forwarder,
          // meta: { roles: ['admin'] } // Only Admin
        },
        {
          path: "destinations",
          name: "Destination",
          component: Destination,
          // meta: { roles: ['admin'] } // Only Admin
        },
        {
          path: "settings",
          name: "Settings",
          component: Settings,
          meta: { roles: ['admin'] } // Only Admin
        },
        // --- SHARED ROUTES ---
        {
          path: "profile",
          name: "Profile",
          component: Profile,
        },
        {
          path: "import-list",
          name: "ImportList",
          component: ImportList,
        },
        {
          path: "total-report", 
          name: "TotalDownloadReport",
          component: TotalDownloadReport,
        },
        {
          path: "auto-download-bot",
          name: "AutoDownloadBot",
          component: AutoDownloadBot,
        },
        {
            path: "invoice-report",
            name: "InvoiceReport",
            component: InvoiceReport,
        },
        
      ],
    },
    {
      path: "/:pathMatch(.*)*",
      name: "NotFound",
      component: NotFound,
    },
  ],
});

// --- HELPER: Parse Token Payload ---
function parseJwt(token) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map(function (c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

// --- HELPER: Check Expiry ---
function isTokenExpired(token) {
  const payload = parseJwt(token);
  if (!payload) return true;
  
  const currentTime = Math.floor(Date.now() / 1000);
  return currentTime > payload.exp;
}

// Workaround for Vite dynamic import errors
router.onError((err, to) => {
  if (err?.message?.includes?.("Failed to fetch dynamically imported module")) {
    if (localStorage.getItem("vuetify:dynamic-reload")) {
      console.error("Dynamic import error, reloading page did not fix it", err);
    } else {
      console.log("Reloading page to fix dynamic import error");
      localStorage.setItem("vuetify:dynamic-reload", "true");
      location.assign(to.fullPath);
    }
  } else {
    console.error(err);
  }
});

router.isReady().then(() => {
  localStorage.removeItem("vuetify:dynamic-reload");
});

// --- AUTH & ROLE GUARD ---
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const token = localStorage.getItem("access_token");

  if (requiresAuth) {
    // 1. Validate Token Existance & Expiry
    if (!token || isTokenExpired(token)) {
      localStorage.removeItem("access_token"); 
      localStorage.removeItem("refresh_token"); 
      return next("/login");
    }

    // 2. Validate Role Access
    // Check if the route has specific role requirements
    const requiredRoles = to.meta.roles;
    if (requiredRoles) {
        const payload = parseJwt(token);
        const userRole = payload.role || payload.user_role || 'user'; 
        
        console.log(`Navigating to ${to.path}. Required: ${requiredRoles}, User Role: ${userRole}`);

        if (!requiredRoles.includes(userRole)) {
            // alert("Access Denied: Admins Only");
            return next('/dashboard');
        }
    }
    
    // 3. Allow Access
    next();

  } else {
    // 4. Public Routes logic
    if (to.path === '/login' && token && !isTokenExpired(token)) {
      next('/dashboard');
    } else {
      next();
    }
  }
});

export default router;