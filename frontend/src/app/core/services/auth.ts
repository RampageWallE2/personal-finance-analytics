import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  message: string;
  user: {
    id: number;
    username: string;
    email: string;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthenticatedUser {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  message: string;
  user: AuthenticatedUser;
}

@Injectable({
  providedIn: 'root',
})
export class Auth {
  private readonly http = inject(HttpClient);

  private readonly apiUrl = 'http://localhost:5000/auth';

  register(
    data: RegisterRequest,
  ): Observable<RegisterResponse> {
    return this.http.post<RegisterResponse>(
      `${this.apiUrl}/register`,
      data,
    );
  }

  login(
    data: LoginRequest,
  ): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(
      `${this.apiUrl}/login`,
      data,
    );
  }

  saveSession(
    response: LoginResponse,
    rememberMe: boolean,
  ): void {
    this.clearSession();

    const storage = rememberMe
      ? localStorage
      : sessionStorage;

    storage.setItem(
      'access_token',
      response.access_token,
    );

    storage.setItem(
      'authenticated_user',
      JSON.stringify(response.user),
    );
  }

  getToken(): string | null {
    return (
      localStorage.getItem('access_token') ??
      sessionStorage.getItem('access_token')
    );
  }

  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  clearSession(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('authenticated_user');

    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('authenticated_user');
  }
}