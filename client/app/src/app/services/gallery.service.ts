import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class GalleryService {

  private apiUrl = 'http://192.168.1.23:5000/gallery';

  constructor(private http: HttpClient) { }

  // Récupérer les photos de l'utilisateur connecté
  getUserPhotos(sortOrder: string = 'recent'): Observable<any> {
    const url = `${this.apiUrl}/gallery/dashboard?sort_order=${sortOrder}`;
    return this.http.get(url);
  }

  // Ajouter une nouvelle photo
  addPhoto(photo: File): Observable<any> {
    const formData = new FormData();
    formData.append('image', photo);

    const headers = new HttpHeaders({
      'enctype': 'multipart/form-data'
    });

    const url = `${this.apiUrl}/gallery/add_photo`;
    return this.http.post(url, formData, { headers });
  }

  // Voir une photo spécifique
  viewPhoto(photoId: number): Observable<Blob> {
    const url = `${this.apiUrl}/gallery/view_photo/${photoId}`;
    return this.http.get(url, { responseType: 'blob' });
  }

  // Modifier le profil de l'utilisateur
  editProfile(profileData: any): Observable<any> {
    const url = `${this.apiUrl}/gallery/edit_profile`;
    return this.http.post(url, profileData);
  }
}
