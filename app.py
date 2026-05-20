from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import random

# ========================
# APP CONFIGURATION
# ========================

app = Flask(__name__)

app.secret_key = 'dcba'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=180)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ========================
# DATABASE MODELS
# ========================

class User(db.Model):
    """Stores registered users (both admin and normal)."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')  # 'user' or 'admin'
 


class Skill(db.Model):
    """Represents a skill (quiz topic)."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)      
    category = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    questions = db.relationship('Question', backref='skill', lazy=True, cascade="all, delete-orphan")


class Question(db.Model):
    """Stores quiz questions under a skill."""
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    answers = db.relationship('Answer', backref='question', lazy=True, cascade="all, delete-orphan")


class Answer(db.Model):
    """Stores possible answers for each question."""
    id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)


class UserAnswer(db.Model):
    """Tracks which answer a user selected for a question."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)

class UserScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # link to user
    user_name = db.Column(db.String(100), nullable=False)                       # just store string
    user_email = db.Column(db.String(100), nullable=False) 
    score = db.Column(db.Integer, nullable=False)                               # just store number
    total = db.Column(db.Integer, nullable=False)                               # just store number
    percentage = db.Column(db.Float, nullable=False)                            # just store float

    

def seed_database():
    # Only seed if we don't have our standard skills set up
    if Skill.query.filter_by(name="Python Programming").first() is None:
        # Clear existing skill/question/answer data to avoid conflicts and gibberish
        db.session.query(Answer).delete()
        db.session.query(Question).delete()
        db.session.query(Skill).delete()
        db.session.commit()

        # Seed data
        skills_data = [
            {
                "name": "Core and Adv.Java",
                "description": "Test your basics and advanced concepts in Java structure, collections, and styling.",
                "category": "Programming",
                "level": "Intermediate",
                "questions": [
                    {
                        "text": "Which collection type does not allow duplicate elements?",
                        "answers": [("Set", True), ("List", False), ("Map", False), ("Queue", False)]
                    },
                    {
                        "text": "What is the purpose of the 'finally' block in Java exception handling?",
                        "answers": [("To execute code regardless of an exception", True), ("To catch exceptions", False), ("To throw exceptions", False), ("To terminate the program", False)]
                    },
                    {
                        "text": "Which design pattern is used to get a single instance of a class?",
                        "answers": [("Singleton", True), ("Factory", False), ("Observer", False), ("Builder", False)]
                    }
                ]
            },
            {
                "name": "Python with SQL",
                "description": "Assess your core understanding of Python and SQL database integration.",
                "category": "Database",
                "level": "Intermediate",
                "questions": [
                    {
                        "text": "Which standard library is used to connect to a SQLite database in Python?",
                        "answers": [("sqlite3", True), ("sqlite", False), ("sql_connect", False), ("db_sqlite", False)]
                    },
                    {
                        "text": "What is the method name used to execute an SQL query via a DB-API cursor?",
                        "answers": [("execute()", True), ("run()", False), ("query()", False), ("commit()", False)]
                    },
                    {
                        "text": "What method must be called to save changes made during a transaction?",
                        "answers": [("commit()", True), ("save()", False), ("execute()", False), ("close()", False)]
                    }
                ]
            },
            {
                "name": "Python Programming",
                "description": "Solve syntax, logic, and code-based Python programming multiple choice questions.",
                "category": "Programming",
                "level": "Intermediate",
                "questions": [
                    {
                        "text": "What is the correct file extension for Python files?",
                        "answers": [(".py", True), (".pyt", False), (".pyw", False), (".pyc", False)]
                    },
                    {
                        "text": "Which of the following is used to define a block of code in Python?",
                        "answers": [("Indentation", True), ("Brackets", False), ("Parentheses", False), ("Keyboards", False)]
                    },
                    {
                        "text": "Which function is used to get the length of a list in Python?",
                        "answers": [("len()", True), ("length()", False), ("count()", False), ("size()", False)]
                    }
                ]
            },
            {
                "name": "Java Frameworks",
                "description": "Test your knowledge of Spring, Hibernate, and common Java ecosystem frameworks.",
                "category": "Programming",
                "level": "Developer Mode",
                "questions": [
                    {
                        "text": "Which annotation is used to mark a class as a Spring Boot application?",
                        "answers": [("@SpringBootApplication", True), ("@SpringApplication", False), ("@BootApplication", False), ("@EnableConfig", False)]
                    },
                    {
                        "text": "In Hibernate, what does ORM stand for?",
                        "answers": [("Object-Relational Mapping", True), ("Object-Resource Manager", False), ("Online Relationship Model", False), ("Open Source Resource", False)]
                    },
                    {
                        "text": "Which of the following is a popular Java build tool?",
                        "answers": [("Maven", True), ("pip", False), ("npm", False), ("cargo", False)]
                    }
                ]
            },
            {
                "name": "Core Java",
                "description": "Questions around Java object-oriented principles, data types, and syntax.",
                "category": "Programming",
                "level": "Mid Level",
                "questions": [
                    {
                        "text": "Which of the following is not a primitive data type in Java?",
                        "answers": [("String", True), ("int", False), ("boolean", False), ("double", False)]
                    },
                    {
                        "text": "Which keyword is used to inherit a class in Java?",
                        "answers": [("extends", True), ("implements", False), ("inherits", False), ("exports", False)]
                    },
                    {
                        "text": "Which method is the entry point for any Java application?",
                        "answers": [("main", True), ("start", False), ("run", False), ("init", False)]
                    }
                ]
            },
            {
                "name": "DOTNET",
                "description": "Questions around full-stack logic, tools, and deployment in the C# / .NET ecosystem.",
                "category": "Programming",
                "level": "Mid Level",
                "questions": [
                    {
                        "text": "What language is primarily used for programming in the .NET framework?",
                        "answers": [("C#", True), ("Java", False), ("Python", False), ("C++", False)]
                    },
                    {
                        "text": "What does CLR stand for in .NET?",
                        "answers": [("Common Language Runtime", True), ("Common Library Repository", False), ("Central Log Reader", False), ("Class Library Reference", False)]
                    },
                    {
                        "text": "Which framework is used for building cross-platform web APIs in modern .NET?",
                        "answers": [("ASP.NET Core", True), ("Silverlight", False), ("WPF", False), ("Windows Forms", False)]
                    }
                ]
            }
        ]

        for s_info in skills_data:
            skill = Skill(name=s_info["name"], description=s_info["description"], category=s_info["category"], level=s_info["level"])
            db.session.add(skill)
            db.session.flush()

            for q_info in s_info["questions"]:
                qn = Question(question_text=q_info["text"], skill=skill)
                db.session.add(qn)
                db.session.flush()

                for a_text, is_corr in q_info["answers"]:
                    ans = Answer(answer_text=a_text, is_correct=is_corr, question=qn)
                    db.session.add(ans)

        db.session.commit()

# Create database tables
with app.app_context():
    db.create_all()
    seed_database()


# ========================
# AUTHENTICATION ROUTES
# ========================

@app.route('/', methods=['GET', 'POST'])
def login():
    """Handles user login (admin or normal)."""
    if 'username' in session:
        return redirect(url_for('admin_dashboard' if session.get('role') == 'admin' else 'home'))

    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            # Store session info
            session.update({
                'username': user.name,
                'email': user.email,
                'role': user.role,
                'user_id': user.id,
                'permanent': True
            })
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for('admin_dashboard' if user.role == 'admin' else 'home'))

        flash("Invalid email or password", "danger")
    return render_template("login.html")


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    """Handles new user registration."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = 'admin' if (email.endswith('@admin.com') or email.endswith('@zeon.com') or 'admin' in email.split('@')[0]) else 'user'

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for('registration'))

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Successfully Registered!", "success")
        return redirect(url_for('login'))

    return render_template("registration.html")


@app.route('/logout')
def logout():
    """Logs the user out."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# ========================
# USER ROUTES
# ========================

@app.route('/home')
def home():
    """Home page for normal users."""
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    skills = Skill.query.all()
    return render_template("home.html", skills=skills, header=True, footer=True)


@app.route('/popularquiz')
def popularquiz():
    """Displays quizzes grouped by category."""
    all_skills = Skill.query.all()
    skills_by_category = {}
    for skill in all_skills:
        skills_by_category.setdefault(skill.category, []).append(skill)

    return render_template(
        "popularquiz.html",
        skills_by_category=skills_by_category,
        categories=skills_by_category.keys(),
        header=True,
        footer=True
    )


@app.route('/testqn/<int:skill_id>')
def testqn(skill_id):
    """Show shuffled questions for a selected skill."""
    if 'username' not in session:
        flash("Please log in to start a quiz.", "warning")
        return redirect(url_for('login'))

    skill = Skill.query.get_or_404(skill_id)
    if not skill.questions:
        flash("This skill has no questions yet.", "warning")
        return redirect(url_for('popularquiz'))

    shuffled_questions = list(skill.questions)
    random.shuffle(shuffled_questions)
    skill.questions = shuffled_questions

    return render_template("testqn.html", skill=skill, footer=True)



@app.route('/test/<int:skill_id>', methods=['POST'])
def test(skill_id):
    # ensure user is logged in
    if 'username' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    skill = Skill.query.get_or_404(skill_id)

    results = []       # will hold per-question info to send to template
    score = 0
    total = len(skill.questions)
    
    # Iterate through each question for the skill.
    # The form inputs must be named "question_<question.id>" and contain an answer id.
    for question in skill.questions:
        ans_id = request.form.get(f'question_{question.id}')  # e.g., 'question_5' -> '12' (answer id) or None
        selected_answer = Answer.query.get(int(ans_id)) if ans_id else None

        # Store user's answer in DB if an answer was selected
        if ans_id:
            user_answer = UserAnswer(user_id=user_id, question_id=question.id, answer_id=int(ans_id))
            db.session.add(user_answer)

        # Prepare display texts
        user_answer_text = selected_answer.answer_text if selected_answer else "Not Answered"

        # Find the correct answer text for this question
        correct_answer_text = None
        for a in question.answers:
            if a.is_correct:
                correct_answer_text = a.answer_text
                break

        # Determine correctness
        is_correct = (selected_answer.is_correct if selected_answer else False)
        if is_correct:
            score += 1
          
        
        
        # Append the structured result for the template
        results.append({
            'question_id': question.id,
            'question': question.question_text,
            'user_answer': user_answer_text,
            'correct_answer': correct_answer_text,
            'is_correct': is_correct
        })
    percentage = (score/total)*100 if total > 0 else 0

    user=User.query.get_or_404(user_id)
    userscore=UserScore(user_id=user_id,user_name=user.name,user_email=user.email,score=score,total=total,percentage=percentage)
    existing_userscore=UserScore.query.filter_by(user_id=user_id).first()
    if existing_userscore:
        db.session.delete(existing_userscore)

    db.session.add(userscore)
    # Commit the saved UserAnswer rows
    db.session.commit()

    # pass/fail threshold (adjust as you like, here 50%)
    passed = (score >= (total * 0.5)) if total > 0 else False

    # Render the results page with all data
    return render_template(
        'testresult.html',
        skill=skill,
        total=total,
        score=score,
        passed=passed,
        results=results
    )


@app.route('/quizview/<int:skill_id>')
def quizview(skill_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    skill = Skill.query.get_or_404(skill_id)
    return render_template("quizview.html", skill=skill, footer=True)


@app.route('/testresult')
def testresult():
    return render_template("testresult.html", footer=True)


@app.route('/viewresult')
def viewresult():
    return render_template("viewresult.html", footer=True)


# ========================
# ADMIN ROUTES
# ========================

@app.route('/admin_dashboard')
def admin_dashboard():
    """Dashboard for admins only."""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("admin_dashboard.html",
                           username=session.get('username'),
                           footer=True, sidebar=True, header=True)


@app.route('/admin_createskill', methods=['GET', 'POST'])
def admin_createskill():
    """Admin: create a new skill with its questions."""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Create skill
        new_skill = Skill(
            name=request.form.get('skill_name'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            level=request.form.get('level')
        )
        db.session.add(new_skill)
        db.session.flush()

        # Add questions & answers
        q_idx = 0
        while f"questions[{q_idx}][text]" in request.form:
            q_text = request.form.get(f"questions[{q_idx}][text]")
            correct_idx = request.form.get(f"questions[{q_idx}][correct_answer]")
            if q_text:
                new_qn = Question(question_text=q_text, skill=new_skill)
                db.session.add(new_qn)
                db.session.flush()

                for i, ans_text in enumerate(request.form.getlist(f"questions[{q_idx}][answers][]")):
                    if ans_text.strip():
                        db.session.add(Answer(answer_text=ans_text.strip(),
                                              is_correct=(str(i) == correct_idx),
                                              question=new_qn))
            q_idx += 1

        db.session.commit()
        flash('New skill with questions added successfully!', 'success')
        return redirect(url_for('admin_allskill'))

    return render_template("admin_createskill.html", footer=True, sidebar=True, header=True)


@app.route('/admin_editskill/<int:skill_id>', methods=['GET', 'POST'])
def admin_editskill(skill_id):
    """Admin: edit skill details."""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    skill = Skill.query.get_or_404(skill_id)

    if request.method == 'POST':
        skill.name = request.form.get('skill_name')
        skill.description = request.form.get('description')
        skill.category = request.form.get('category')
        skill.level = request.form.get('level')
        db.session.commit()
        flash('Skill details updated successfully!', 'success')
        return redirect(url_for('admin_editskill', skill_id=skill.id))

    return render_template("admin_editskill.html", skill=skill, footer=True, sidebar=True, header=True)


@app.route('/admin_add_question/<int:skill_id>', methods=['POST'])
def admin_add_question(skill_id):
    """Admin: add a new question to a skill."""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    skill = Skill.query.get_or_404(skill_id)
    q_text = request.form.get('new_question_text')
    answers = request.form.getlist('new_answers[]')
    correct_index = request.form.get('new_correct_answer')

    if q_text and len(answers) == 4 and correct_index is not None:
        new_qn = Question(question_text=q_text, skill=skill)
        db.session.add(new_qn)
        db.session.flush()
        for i, ans_text in enumerate(answers):
            db.session.add(Answer(answer_text=ans_text.strip(),
                                  is_correct=(str(i) == correct_index),
                                  question=new_qn))
        db.session.commit()
        flash('New question added successfully!', 'success')
    else:
        flash('Failed to add question. Fill all fields.', 'danger')

    return redirect(url_for('admin_editskill', skill_id=skill.id))


@app.route('/admin_update_question/<int:question_id>', methods=['POST'])
def admin_update_question(question_id):
    qn = Question.query.get_or_404(question_id)

    question_text = request.form.get('question_text', '').strip()
    if not question_text:
        flash("Question text cannot be empty!", "danger")
        return redirect(url_for('admin_editskill', skill_id=qn.skill_id))

    qn.question_text = question_text

    # Update answers
    for ans in qn.answers:
        ans_text = request.form.get(f'answer_text_{ans.id}', '').strip()
        if not ans_text:
            flash("Answer text cannot be empty!", "danger")
            return redirect(url_for('admin_editskill', skill_id=qn.skill_id))
        ans.answer_text = ans_text
        ans.is_correct = (str(ans.id) == request.form.get("correct_answer"))

    db.session.commit()
    flash("Question updated successfully!", "success")
    return redirect(url_for('admin_editskill', skill_id=qn.skill_id))



@app.route('/admin_delete_question/<int:question_id>', methods=['POST'])
def admin_delete_question(question_id):
    """Admin: delete a question."""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    qn = Question.query.get_or_404(question_id)
    skill_id = qn.skill_id
    db.session.delete(qn)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin_editskill', skill_id=skill_id))


@app.route('/admin_deleteskill/<int:skill_id>', methods=['POST'])
def admin_deleteskill(skill_id):
    """Admin: delete a whole skill."""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    skill = Skill.query.get_or_404(skill_id)
    db.session.delete(skill)
    db.session.commit()
    flash(f'Skill "{skill.name}" deleted.', 'success')
    return redirect(url_for('admin_allskill'))


@app.route('/admin_categories')
def admin_categories():
    return render_template("admin_categories.html", footer=True, sidebar=True, header=True)


@app.route('/admin_allskill')
def admin_allskill():
    """Admin: view all skills."""
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    all_skills = Skill.query.all()
    return render_template("admin_allskill.html", skills=all_skills, footer=True, sidebar=True, header=True)


@app.route('/admin_viewresults')
def admin_viewresults():
    return render_template("admin_viewresults.html", footer=True, sidebar=True, header=True)


@app.route('/admin_skillresults')
def admin_skillresults():
    # Admin check
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    # Fetch all user scores
    user_scores = UserScore.query.order_by(UserScore.percentage.desc()).all()
 

    return render_template(
        "admin_skillresults.html",
        user_scores=user_scores,
        footer=True,
        sidebar=True,
        header=True
    )


# ========================
# APP ENTRY POINT
# ========================

if __name__ == '__main__':
    app.run(debug=True)
