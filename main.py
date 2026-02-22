from fastapi import FastAPI, Request, Form, status,  Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from model.parse import SeedDatabase
from model.dashboard import GetDashboard
from model.recommend import RecommendSystem
from model.register import Register
from model.profile import Profile
from model.login import Login, COOKIE_NAME, COOKIE_MAX_AGE
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/parse")
async def seed_database():
    SeedDatabase.seed()

    return RedirectResponse(url="/", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    dashboard = GetDashboard.get_dashboard()

    return templates.TemplateResponse("base.html", {
        "request":request,
        "dashboard": dashboard
        })


@app.get("/recommend", response_class=HTMLResponse)
async def create_profile(request: Request, user_id: Optional[int] = Depends(Login.get_current_user_id)):
    recommendations = RecommendSystem.recommend(user_id=user_id)
    return templates.TemplateResponse("recommend.html", {
        "request": request,
        "recommendations": recommendations
    })

@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})


@app.post("/registration_form")
async def registration_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password_repeat: str = Form(...)
):
    if password != password_repeat:
        return templates.TemplateResponse("registration.html", {
            "request": request,
            "form_error": "Пароли не совпадают",
            "username": username
        }, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    ok = Register.reg(username, password)
    if ok:
        return RedirectResponse(url="/login", status_code=303)
    else:
        return templates.TemplateResponse("registration.html", {
            "request": request,
            "form_error": "Регистрация не удалась (пользователь с таким именем уже существует)",
            "username": username
        }, status_code=status.HTTP_400_BAD_REQUEST)


@app.get("/login", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login_form")
async def login_form(
    request: Request,
    username: str = Form(...), 
    password: str = Form(...)
):
    user_id = Login.login(username, password)
    if not user_id:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "form_error": "Invalid credentials"
        }, status_code=status.HTTP_401_UNAUTHORIZED)

    cookie_value = Login.create_session_cookie_value(user_id)
    print("LOGIN: setting cookie:", cookie_value)
    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=cookie_value,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return response

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, user_id: Optional[int] = Depends(Login.get_current_user_id)):
    if user_id is None:
        return RedirectResponse(url="/login", status_code=303)

    chips = Profile.get_chips()
    user_chips = Profile.search_profile(user_id=user_id)
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "chips": chips,
        "user_chips": user_chips
    })


class SelectedChips(BaseModel):
    values: list[str]
    ids: list[int]

@app.post("/save-chips")
async def save_chips(
    payload: SelectedChips,
    user_id: Optional[int] = Depends(Login.get_current_user_id)
):
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пожалуйста, войдите в систему"
        )

    ids: list[int] = payload.ids
    Profile.apply_chips(user_id=user_id, ids=ids)

    return {"ok": True, "saved_count": len(ids)}

@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response