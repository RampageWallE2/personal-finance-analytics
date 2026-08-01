import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';

import { Auth } from '../../../core/services/auth';

const passwordsMatchValidator: ValidatorFn = (
  control: AbstractControl,
): ValidationErrors | null => {
  const password = control.get('password')?.value;
  const confirmPassword = control.get('confirmPassword')?.value;

  return password === confirmPassword
    ? null
    : { passwordsDoNotMatch: true };
};

@Component({
  selector: 'app-register',
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
  templateUrl: './register.html',
  styleUrl: './register.scss',
})
export class Register {
  private readonly formBuilder = inject(FormBuilder);
  private readonly authService = inject(Auth);

  hidePassword = true;
  hideConfirmPassword = true;

  isSubmitting = false;
  successMessage = '';
  errorMessage = '';

  readonly registerForm = this.formBuilder.nonNullable.group(
    {
      username: [
        '',
        [
          Validators.required,
          Validators.minLength(3),
          Validators.maxLength(30),
        ],
      ],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
      acceptTerms: [false, Validators.requiredTrue],
    },
    {
      validators: passwordsMatchValidator,
    },
  );

  get username() {
    return this.registerForm.controls.username;
  }

  get email() {
    return this.registerForm.controls.email;
  }

  get password() {
    return this.registerForm.controls.password;
  }

  get confirmPassword() {
    return this.registerForm.controls.confirmPassword;
  }

  onSubmit(): void {
    this.successMessage = '';
    this.errorMessage = '';

    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    const {
      username,
      email,
      password,
    } = this.registerForm.getRawValue();

    const userData = {
      username: username.trim(),
      email: email.trim().toLowerCase(),
      password,
    };

    this.isSubmitting = true;

    this.authService
      .register(userData)
      .pipe(
        finalize(() => {
          this.isSubmitting = false;
        }),
      )
      .subscribe({
        next: (response) => {
          this.successMessage = response.message;
          this.registerForm.reset();
        },
        error: (error: HttpErrorResponse) => {
          this.errorMessage = this.getErrorMessage(error);
        },
      });
  }

  private getErrorMessage(error: HttpErrorResponse): string {
    const backendMessage = error.error?.message;

    if (typeof backendMessage === 'string') {
      return backendMessage;
    }

    if (error.status === 0) {
      return 'No se pudo conectar con el servidor.';
    }

    if (error.status === 409) {
      return 'El nombre de usuario o correo ya está registrado.';
    }

    return 'No se pudo crear la cuenta. Inténtalo nuevamente.';
  }
}