import { Routes } from '@angular/router';

import { Home } from './features/home/home';
import { Register } from './features/auth/register/register';
import { Login } from './features/auth/login/login';
import { Dashboard } from './features/dashboard/dashboard';

export const routes: Routes = [
    {
        path: '',
        component: Home,
        title: 'Inicio | Personal Finance Analytics'
    },
    {
        path: 'login',
        component: Login,
        title: 'Login | Personal Finance Analytics'
    },
    {
        path: 'register',
        component: Register,
        title: 'Register | Personal Finance Analytics'
    },
    {
        path: 'dashboard',
        component: Dashboard,
        title: 'Dashboad | Personal Finance Analytics'
    },
    {
        path: '**',
        redirectTo: '',
    }
];
