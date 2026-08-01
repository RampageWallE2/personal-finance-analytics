import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {
  Router,
  RouterLink,
} from '@angular/router';
import { finalize } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';

import { Auth } from '../../../core/services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
  ],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  private readonly formBuilder = inject(FormBuilder);
  private readonly authService = inject(Auth);
  private readonly router = inject(Router);

  hidePassword = true;
  isSubmitting = false;
  errorMessage = '';

  readonly loginForm = this.formBuilder.nonNullable.group({
    email: [
      '',
      [
        Validators.required,
        Validators.email,
      ],
    ],
    password: [
      '',
      Validators.required,
    ],
    rememberMe: [false],
  });

  get email() {
    return this.loginForm.controls.email;
  }

  get password() {
    return this.loginForm.controls.password;
  }

  onSubmit(): void {
    this.errorMessage = '';

    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    const {
      email,
      password,
      rememberMe,
    } = this.loginForm.getRawValue();

    this.isSubmitting = true;

    this.authService
      .login({
        email: email.trim().toLowerCase(),
        password,
      })
      .pipe(
        finalize(() => {
          this.isSubmitting = false;
        }),
      )
      .subscribe({
        next: (response) => {
          this.authService.saveSession(
            response,
            rememberMe,
          );

          void this.router.navigateByUrl('/dashboard');
        },

        error: (error: HttpErrorResponse) => {
          this.errorMessage =
            this.getErrorMessage(error);
        },
      });
  }

  private getErrorMessage(
    error: HttpErrorResponse,
  ): string {
    const backendMessage = error.error?.message;

    if (typeof backendMessage === 'string') {
      return backendMessage;
    }

    if (error.status === 0) {
      return 'No se pudo conectar con el servidor.';
    }

    if (error.status === 400) {
      return 'Completa correctamente los datos.';
    }

    if (error.status === 401) {
      return 'Correo o contraseña incorrectos.';
    }

    return 'No se pudo iniciar sesión. Inténtalo nuevamente.';
  }
}