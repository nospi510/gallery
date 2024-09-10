import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

interface LoginResponse {
  message: string;
  status: string;
  redirect?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://192.168.1.23:5000/auth';

  constructor(private http: HttpClient) {}

  login(username: string, password: string): Observable<LoginResponse> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    const body = { username, password };
    return this.http.post<LoginResponse>(`${this.apiUrl}/login`, body, { headers });
  }

  register(username: string, password: string, role: string): Observable<LoginResponse> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    const body = { username, password, role };
    return this.http.post<LoginResponse>(`${this.apiUrl}/register`, body, { headers });
  }

  logout(): Observable<LoginResponse> {
    return this.http.get<LoginResponse>(`${this.apiUrl}/logout`);
  }
}
