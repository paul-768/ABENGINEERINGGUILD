# seed_100_achievements.py
import json
import os
from app import create_app, db
from app.models import Achievement, UserAchievement
from sqlalchemy import text

# The complete 100 achievements data with all icons
ACHIEVEMENTS_100 = [
    # QUIZ & PERFORMANCE (1-20)
    {"name": "First Step", "description": "Complete your first quiz", "icon": "fas fa-flag-checkered", "points": 10, "category": "quiz", "requirement_type": "quiz_count", "requirement_value": 1, "badge_color": "green", "display_order": 1},
    {"name": "Getting Started", "description": "Complete 5 quizzes", "icon": "fas fa-rocket", "points": 15, "category": "quiz", "requirement_type": "quiz_count", "requirement_value": 5, "badge_color": "blue", "display_order": 2},
    {"name": "Quiz Enthusiast", "description": "Complete 10 quizzes", "icon": "fas fa-clipboard-list", "points": 25, "category": "quiz", "requirement_type": "quiz_count", "requirement_value": 10, "badge_color": "purple", "display_order": 3},
    {"name": "Dedicated Learner", "description": "Complete 25 quizzes", "icon": "fas fa-graduation-cap", "points": 40, "category": "quiz", "requirement_type": "quiz_count", "requirement_value": 25, "badge_color": "indigo", "display_order": 4},
    {"name": "Quiz Master", "description": "Complete 50 quizzes", "icon": "fas fa-crown", "points": 60, "category": "quiz", "requirement_type": "quiz_count", "requirement_value": 50, "badge_color": "yellow", "display_order": 5},
    {"name": "Quiz Legend", "description": "Complete 100 quizzes", "icon": "fas fa-star-of-life", "points": 100, "category": "quiz", "requirement_type": "quiz_count", "requirement_value": 100, "badge_color": "red", "display_order": 6},
    {"name": "Perfect Score", "description": "Get 100% on any quiz", "icon": "fas fa-check-double", "points": 20, "category": "quiz", "requirement_type": "perfect_score", "requirement_value": 1, "badge_color": "yellow", "display_order": 7},
    {"name": "Perfect x3", "description": "Get 3 perfect scores", "icon": "fas fa-medal", "points": 30, "category": "quiz", "requirement_type": "perfect_score", "requirement_value": 3, "badge_color": "blue", "display_order": 8},
    {"name": "Perfect x5", "description": "Get 5 perfect scores", "icon": "fas fa-trophy", "points": 50, "category": "quiz", "requirement_type": "perfect_score", "requirement_value": 5, "badge_color": "purple", "display_order": 9},
    {"name": "Perfect Streak", "description": "Get 10 perfect scores", "icon": "fas fa-crown", "points": 80, "category": "quiz", "requirement_type": "perfect_score", "requirement_value": 10, "badge_color": "yellow", "display_order": 10},
    {"name": "High Achiever", "description": "Average score of 85% or higher", "icon": "fas fa-chart-line", "points": 25, "category": "quiz", "requirement_type": "high_score", "requirement_value": 85, "badge_color": "green", "display_order": 11},
    {"name": "Top Performer", "description": "Average score of 90% or higher", "icon": "fas fa-chart-line", "points": 40, "category": "quiz", "requirement_type": "high_score", "requirement_value": 90, "badge_color": "blue", "display_order": 12},
    {"name": "Elite Scorer", "description": "Average score of 95% or higher", "icon": "fas fa-crown", "points": 60, "category": "quiz", "requirement_type": "high_score", "requirement_value": 95, "badge_color": "purple", "display_order": 13},
    {"name": "Question Warrior", "description": "Answer 500 questions", "icon": "fas fa-brain", "points": 30, "category": "quiz", "requirement_type": "total_questions", "requirement_value": 500, "badge_color": "green", "display_order": 14},
    {"name": "Knowledge Seeker", "description": "Answer 1,000 questions", "icon": "fas fa-book-reader", "points": 50, "category": "quiz", "requirement_type": "total_questions", "requirement_value": 1000, "badge_color": "blue", "display_order": 15},
    {"name": "Question Master", "description": "Answer 5,000 questions", "icon": "fas fa-database", "points": 80, "category": "quiz", "requirement_type": "total_questions", "requirement_value": 5000, "badge_color": "purple", "display_order": 16},
    {"name": "Walking Encyclopedia", "description": "Answer 10,000 questions", "icon": "fas fa-university", "points": 120, "category": "quiz", "requirement_type": "total_questions", "requirement_value": 10000, "badge_color": "yellow", "display_order": 17},
    {"name": "Time Keeper", "description": "Spend 10 hours studying", "icon": "fas fa-hourglass-half", "points": 25, "category": "quiz", "requirement_type": "time_spent", "requirement_value": 600, "badge_color": "green", "display_order": 18},
    {"name": "Study Warrior", "description": "Spend 50 hours studying", "icon": "fas fa-clock", "points": 60, "category": "quiz", "requirement_type": "time_spent", "requirement_value": 3000, "badge_color": "blue", "display_order": 19},
    {"name": "Dedicated Scholar", "description": "Spend 100 hours studying", "icon": "fas fa-user-graduate", "points": 100, "category": "quiz", "requirement_type": "time_spent", "requirement_value": 6000, "badge_color": "purple", "display_order": 20},
    
    # STREAK (21-30)
    {"name": "3-Day Streak", "description": "Study for 3 days in a row", "icon": "fas fa-calendar-day", "points": 10, "category": "streak", "requirement_type": "streak", "requirement_value": 3, "badge_color": "green", "display_order": 21},
    {"name": "7-Day Streak", "description": "Study for 7 days in a row", "icon": "fas fa-calendar-week", "points": 20, "category": "streak", "requirement_type": "streak", "requirement_value": 7, "badge_color": "blue", "display_order": 22},
    {"name": "14-Day Streak", "description": "Study for 14 days in a row", "icon": "fas fa-calendar-alt", "points": 35, "category": "streak", "requirement_type": "streak", "requirement_value": 14, "badge_color": "purple", "display_order": 23},
    {"name": "30-Day Streak", "description": "Study for 30 days in a row", "icon": "fas fa-calendar-check", "points": 50, "category": "streak", "requirement_type": "streak", "requirement_value": 30, "badge_color": "indigo", "display_order": 24},
    {"name": "60-Day Streak", "description": "Study for 60 days in a row", "icon": "fas fa-fire", "points": 75, "category": "streak", "requirement_type": "streak", "requirement_value": 60, "badge_color": "orange", "display_order": 25},
    {"name": "100-Day Streak", "description": "Study for 100 days in a row", "icon": "fas fa-star", "points": 100, "category": "streak", "requirement_type": "streak", "requirement_value": 100, "badge_color": "yellow", "display_order": 26},
    {"name": "Weekend Warrior", "description": "Study on 10 different days", "icon": "fas fa-calendar-weekend", "points": 15, "category": "streak", "requirement_type": "study_days", "requirement_value": 10, "badge_color": "green", "display_order": 27},
    {"name": "Month Master", "description": "Study on 30 different days", "icon": "fas fa-calendar-month", "points": 30, "category": "streak", "requirement_type": "study_days", "requirement_value": 30, "badge_color": "blue", "display_order": 28},
    {"name": "Semester Scholar", "description": "Study on 100 different days", "icon": "fas fa-calendar-plus", "points": 60, "category": "streak", "requirement_type": "study_days", "requirement_value": 100, "badge_color": "purple", "display_order": 29},
    {"name": "Year Round", "description": "Study on 365 different days", "icon": "fas fa-calendar-year", "points": 100, "category": "streak", "requirement_type": "study_days", "requirement_value": 365, "badge_color": "yellow", "display_order": 30},
    
    # AREA I - FARM MACHINERY (31-40)
    {"name": "Farm Apprentice", "description": "Score 70% or higher in Farm Machinery", "icon": "fas fa-tractor", "points": 20, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 70, "requirement_extra": "1", "badge_color": "green", "display_order": 31},
    {"name": "Farm Hand", "description": "Score 80% or higher in Farm Machinery", "icon": "fas fa-tractor", "points": 30, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 80, "requirement_extra": "1", "badge_color": "blue", "display_order": 32},
    {"name": "Machinery Operator", "description": "Score 90% or higher in Farm Machinery", "icon": "fas fa-tractor", "points": 40, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 90, "requirement_extra": "1", "badge_color": "purple", "display_order": 33},
    {"name": "Farm Machinery Expert", "description": "Score 95% or higher in Farm Machinery", "icon": "fas fa-certificate", "points": 50, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 95, "requirement_extra": "1", "badge_color": "yellow", "display_order": 34},
    {"name": "Farm Machinery Starter", "description": "Complete 5 quizzes in Farm Machinery", "icon": "fas fa-play", "points": 15, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 5, "requirement_extra": "1", "badge_color": "green", "display_order": 35},
    {"name": "Farm Machinery Enthusiast", "description": "Complete 10 quizzes in Farm Machinery", "icon": "fas fa-heart", "points": 25, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 10, "requirement_extra": "1", "badge_color": "blue", "display_order": 36},
    {"name": "Farm Machinery Master", "description": "Complete 25 quizzes in Farm Machinery", "icon": "fas fa-crown", "points": 40, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 25, "requirement_extra": "1", "badge_color": "purple", "display_order": 37},
    {"name": "Farm Machinery Perfectionist", "description": "Get a perfect score in Farm Machinery", "icon": "fas fa-star", "points": 50, "category": "mastery", "requirement_type": "topic_perfect_score", "requirement_value": 1, "requirement_extra": "1", "badge_color": "yellow", "display_order": 38},
    {"name": "Farm Equipment Guru", "description": "Complete all questions in Farm Machinery", "icon": "fas fa-database", "points": 60, "category": "mastery", "requirement_type": "topic_completion", "requirement_value": 100, "requirement_extra": "1", "badge_color": "indigo", "display_order": 39},
    {"name": "Machinery Champion", "description": "Average 90% or higher on 20+ Farm Machinery quizzes", "icon": "fas fa-trophy", "points": 70, "category": "mastery", "requirement_type": "topic_high_avg", "requirement_value": 90, "requirement_extra": "1", "badge_color": "yellow", "display_order": 40},
    
    # AREA II - SOIL & WATER (41-50)
    {"name": "Soil Scout", "description": "Score 70% or higher in Soil & Water Management", "icon": "fas fa-tint", "points": 20, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 70, "requirement_extra": "2", "badge_color": "green", "display_order": 41},
    {"name": "Water Watcher", "description": "Score 80% or higher in Soil & Water Management", "icon": "fas fa-water", "points": 30, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 80, "requirement_extra": "2", "badge_color": "blue", "display_order": 42},
    {"name": "Soil Scientist", "description": "Score 90% or higher in Soil & Water Management", "icon": "fas fa-flask", "points": 40, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 90, "requirement_extra": "2", "badge_color": "purple", "display_order": 43},
    {"name": "Water Resource Expert", "description": "Score 95% or higher in Soil & Water Management", "icon": "fas fa-certificate", "points": 50, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 95, "requirement_extra": "2", "badge_color": "yellow", "display_order": 44},
    {"name": "Soil Sampler", "description": "Complete 5 quizzes in Soil & Water Management", "icon": "fas fa-play", "points": 15, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 5, "requirement_extra": "2", "badge_color": "green", "display_order": 45},
    {"name": "Irrigation Specialist", "description": "Complete 10 quizzes in Soil & Water Management", "icon": "fas fa-sprinkler", "points": 25, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 10, "requirement_extra": "2", "badge_color": "blue", "display_order": 46},
    {"name": "Watershed Warrior", "description": "Complete 25 quizzes in Soil & Water Management", "icon": "fas fa-mountain", "points": 40, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 25, "requirement_extra": "2", "badge_color": "purple", "display_order": 47},
    {"name": "Soil Conservationist", "description": "Get a perfect score in Soil & Water Management", "icon": "fas fa-star", "points": 50, "category": "mastery", "requirement_type": "topic_perfect_score", "requirement_value": 1, "requirement_extra": "2", "badge_color": "yellow", "display_order": 48},
    {"name": "Water Management Master", "description": "Complete all questions in Soil & Water Management", "icon": "fas fa-database", "points": 60, "category": "mastery", "requirement_type": "topic_completion", "requirement_value": 100, "requirement_extra": "2", "badge_color": "indigo", "display_order": 49},
    {"name": "Soil & Water Champion", "description": "Average 90% or higher on 20+ Soil & Water quizzes", "icon": "fas fa-trophy", "points": 70, "category": "mastery", "requirement_type": "topic_high_avg", "requirement_value": 90, "requirement_extra": "2", "badge_color": "yellow", "display_order": 50},
    
    # AREA III - POST-HARVEST (51-60)
    {"name": "Harvester Helper", "description": "Score 70% or higher in Post-Harvest Technology", "icon": "fas fa-boxes", "points": 20, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 70, "requirement_extra": "3", "badge_color": "green", "display_order": 51},
    {"name": "Grain Handler", "description": "Score 80% or higher in Post-Harvest Technology", "icon": "fas fa-warehouse", "points": 30, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 80, "requirement_extra": "3", "badge_color": "blue", "display_order": 52},
    {"name": "Post-Harvest Pro", "description": "Score 90% or higher in Post-Harvest Technology", "icon": "fas fa-industry", "points": 40, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 90, "requirement_extra": "3", "badge_color": "purple", "display_order": 53},
    {"name": "Storage Specialist", "description": "Score 95% or higher in Post-Harvest Technology", "icon": "fas fa-certificate", "points": 50, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 95, "requirement_extra": "3", "badge_color": "yellow", "display_order": 54},
    {"name": "Drying Expert", "description": "Complete 5 quizzes in Post-Harvest Technology", "icon": "fas fa-sun", "points": 15, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 5, "requirement_extra": "3", "badge_color": "green", "display_order": 55},
    {"name": "Milling Master", "description": "Complete 10 quizzes in Post-Harvest Technology", "icon": "fas fa-cogs", "points": 25, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 10, "requirement_extra": "3", "badge_color": "blue", "display_order": 56},
    {"name": "Processing Pro", "description": "Complete 25 quizzes in Post-Harvest Technology", "icon": "fas fa-microchip", "points": 40, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 25, "requirement_extra": "3", "badge_color": "purple", "display_order": 57},
    {"name": "Quality Controller", "description": "Get a perfect score in Post-Harvest Technology", "icon": "fas fa-star", "points": 50, "category": "mastery", "requirement_type": "topic_perfect_score", "requirement_value": 1, "requirement_extra": "3", "badge_color": "yellow", "display_order": 58},
    {"name": "Post-Harvest Guru", "description": "Complete all questions in Post-Harvest Technology", "icon": "fas fa-database", "points": 60, "category": "mastery", "requirement_type": "topic_completion", "requirement_value": 100, "requirement_extra": "3", "badge_color": "indigo", "display_order": 59},
    {"name": "Post-Harvest Champion", "description": "Average 90% or higher on 20+ Post-Harvest quizzes", "icon": "fas fa-trophy", "points": 70, "category": "mastery", "requirement_type": "topic_high_avg", "requirement_value": 90, "requirement_extra": "3", "badge_color": "yellow", "display_order": 60},
    
    # ENGINEERING MATH (61-70)
    {"name": "Math Beginner", "description": "Score 70% or higher in Engineering Mathematics", "icon": "fas fa-calculator", "points": 20, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 70, "requirement_extra": "4", "badge_color": "green", "display_order": 61},
    {"name": "Equation Solver", "description": "Score 80% or higher in Engineering Mathematics", "icon": "fas fa-square-root-variable", "points": 30, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 80, "requirement_extra": "4", "badge_color": "blue", "display_order": 62},
    {"name": "Math Wizard", "description": "Score 90% or higher in Engineering Mathematics", "icon": "fas fa-hat-wizard", "points": 40, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 90, "requirement_extra": "4", "badge_color": "purple", "display_order": 63},
    {"name": "Calculus Master", "description": "Score 95% or higher in Engineering Mathematics", "icon": "fas fa-chart-line", "points": 50, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 95, "requirement_extra": "4", "badge_color": "yellow", "display_order": 64},
    {"name": "Number Cruncher", "description": "Complete 5 quizzes in Engineering Mathematics", "icon": "fas fa-play", "points": 15, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 5, "requirement_extra": "4", "badge_color": "green", "display_order": 65},
    {"name": "Formula Finder", "description": "Complete 10 quizzes in Engineering Mathematics", "icon": "fas fa-gear", "points": 25, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 10, "requirement_extra": "4", "badge_color": "blue", "display_order": 66},
    {"name": "Algebraic Ace", "description": "Complete 25 quizzes in Engineering Mathematics", "icon": "fas fa-crown", "points": 40, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 25, "requirement_extra": "4", "badge_color": "purple", "display_order": 67},
    {"name": "Mathlete", "description": "Get a perfect score in Engineering Mathematics", "icon": "fas fa-star", "points": 50, "category": "mastery", "requirement_type": "topic_perfect_score", "requirement_value": 1, "requirement_extra": "4", "badge_color": "yellow", "display_order": 68},
    {"name": "Engineering Math Expert", "description": "Complete all questions in Engineering Mathematics", "icon": "fas fa-database", "points": 60, "category": "mastery", "requirement_type": "topic_completion", "requirement_value": 100, "requirement_extra": "4", "badge_color": "indigo", "display_order": 69},
    {"name": "Math Champion", "description": "Average 90% or higher on 20+ Math quizzes", "icon": "fas fa-trophy", "points": 70, "category": "mastery", "requirement_type": "topic_high_avg", "requirement_value": 90, "requirement_extra": "4", "badge_color": "yellow", "display_order": 70},
    
    # PAES STANDARDS (71-80)
    {"name": "PAES Reader", "description": "Score 70% or higher in PAES Standards", "icon": "fas fa-file-alt", "points": 20, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 70, "requirement_extra": "5", "badge_color": "green", "display_order": 71},
    {"name": "Standard Seeker", "description": "Score 80% or higher in PAES Standards", "icon": "fas fa-book", "points": 30, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 80, "requirement_extra": "5", "badge_color": "blue", "display_order": 72},
    {"name": "Code Enforcer", "description": "Score 90% or higher in PAES Standards", "icon": "fas fa-gavel", "points": 40, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 90, "requirement_extra": "5", "badge_color": "purple", "display_order": 73},
    {"name": "PAES Expert", "description": "Score 95% or higher in PAES Standards", "icon": "fas fa-certificate", "points": 50, "category": "mastery", "requirement_type": "topic_mastery", "requirement_value": 95, "requirement_extra": "5", "badge_color": "yellow", "display_order": 74},
    {"name": "Standard Scout", "description": "Complete 5 quizzes in PAES Standards", "icon": "fas fa-play", "points": 15, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 5, "requirement_extra": "5", "badge_color": "green", "display_order": 75},
    {"name": "Code Collector", "description": "Complete 10 quizzes in PAES Standards", "icon": "fas fa-folder-open", "points": 25, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 10, "requirement_extra": "5", "badge_color": "blue", "display_order": 76},
    {"name": "Regulation Reader", "description": "Complete 25 quizzes in PAES Standards", "icon": "fas fa-scale-balanced", "points": 40, "category": "mastery", "requirement_type": "topic_quiz_count", "requirement_value": 25, "requirement_extra": "5", "badge_color": "purple", "display_order": 77},
    {"name": "PAES Perfectionist", "description": "Get a perfect score in PAES Standards", "icon": "fas fa-star", "points": 50, "category": "mastery", "requirement_type": "topic_perfect_score", "requirement_value": 1, "requirement_extra": "5", "badge_color": "yellow", "display_order": 78},
    {"name": "PAES Master", "description": "Complete all questions in PAES Standards", "icon": "fas fa-database", "points": 60, "category": "mastery", "requirement_type": "topic_completion", "requirement_value": 100, "requirement_extra": "5", "badge_color": "indigo", "display_order": 79},
    {"name": "PAES Champion", "description": "Average 90% or higher on 20+ PAES quizzes", "icon": "fas fa-trophy", "points": 70, "category": "mastery", "requirement_type": "topic_high_avg", "requirement_value": 90, "requirement_extra": "5", "badge_color": "yellow", "display_order": 80},
    
    # SOCIAL (81-90)
    {"name": "First Friend", "description": "Make your first friend", "icon": "fas fa-user-plus", "points": 10, "category": "social", "requirement_type": "friends_count", "requirement_value": 1, "badge_color": "green", "display_order": 81},
    {"name": "Social Butterfly", "description": "Make 5 friends", "icon": "fas fa-butterfly", "points": 20, "category": "social", "requirement_type": "friends_count", "requirement_value": 5, "badge_color": "pink", "display_order": 82},
    {"name": "Community Builder", "description": "Make 10 friends", "icon": "fas fa-users", "points": 35, "category": "social", "requirement_type": "friends_count", "requirement_value": 10, "badge_color": "purple", "display_order": 83},
    {"name": "Networking Pro", "description": "Make 20 friends", "icon": "fas fa-network-wired", "points": 50, "category": "social", "requirement_type": "friends_count", "requirement_value": 20, "badge_color": "blue", "display_order": 84},
    {"name": "First Post", "description": "Create your first post", "icon": "fas fa-pen", "points": 10, "category": "social", "requirement_type": "posts_count", "requirement_value": 1, "badge_color": "green", "display_order": 85},
    {"name": "Active Contributor", "description": "Create 10 posts", "icon": "fas fa-pen-alt", "points": 25, "category": "social", "requirement_type": "posts_count", "requirement_value": 10, "badge_color": "blue", "display_order": 86},
    {"name": "Engaged Citizen", "description": "Create 50 posts", "icon": "fas fa-newspaper", "points": 50, "category": "social", "requirement_type": "posts_count", "requirement_value": 50, "badge_color": "purple", "display_order": 87},
    {"name": "First Comment", "description": "Leave your first comment", "icon": "fas fa-comment", "points": 5, "category": "social", "requirement_type": "comments_count", "requirement_value": 1, "badge_color": "green", "display_order": 88},
    {"name": "Discussion Starter", "description": "Leave 25 comments", "icon": "fas fa-comments", "points": 20, "category": "social", "requirement_type": "comments_count", "requirement_value": 25, "badge_color": "blue", "display_order": 89},
    {"name": "Community Leader", "description": "Leave 100 comments", "icon": "fas fa-chalkboard-user", "points": 40, "category": "social", "requirement_type": "comments_count", "requirement_value": 100, "badge_color": "purple", "display_order": 90},
    
    # SPECIAL / MASTERY (91-100)
    {"name": "All-Rounder", "description": "Score 80% or higher in all topics", "icon": "fas fa-globe", "points": 50, "category": "special", "requirement_type": "all_topics_mastery", "requirement_value": 80, "badge_color": "green", "display_order": 91},
    {"name": "True Scholar", "description": "Score 85% or higher in all topics", "icon": "fas fa-graduation-cap", "points": 75, "category": "special", "requirement_type": "all_topics_mastery", "requirement_value": 85, "badge_color": "blue", "display_order": 92},
    {"name": "Renaissance Engineer", "description": "Score 90% or higher in all topics", "icon": "fas fa-microscope", "points": 100, "category": "special", "requirement_type": "all_topics_mastery", "requirement_value": 90, "badge_color": "purple", "display_order": 93},
    {"name": "Board Exam Ready", "description": "Score 95% or higher in all topics", "icon": "fas fa-clipboard", "points": 150, "category": "special", "requirement_type": "all_topics_mastery", "requirement_value": 95, "badge_color": "yellow", "display_order": 94},
    {"name": "Top 50", "description": "Rank in the top 50 on the scoreboard", "icon": "fas fa-ranking-star", "points": 30, "category": "special", "requirement_type": "rank_position", "requirement_value": 50, "badge_color": "green", "display_order": 95},
    {"name": "Top 25", "description": "Rank in the top 25 on the scoreboard", "icon": "fas fa-medal", "points": 50, "category": "special", "requirement_type": "rank_position", "requirement_value": 25, "badge_color": "blue", "display_order": 96},
    {"name": "Top 10", "description": "Rank in the top 10 on the scoreboard", "icon": "fas fa-trophy", "points": 75, "category": "special", "requirement_type": "rank_position", "requirement_value": 10, "badge_color": "purple", "display_order": 97},
    {"name": "Top 5", "description": "Rank in the top 5 on the scoreboard", "icon": "fas fa-crown", "points": 100, "category": "special", "requirement_type": "rank_position", "requirement_value": 5, "badge_color": "yellow", "display_order": 98},
    {"name": "Number 1", "description": "Achieve the #1 rank on the scoreboard", "icon": "fas fa-star-of-life", "points": 150, "category": "special", "requirement_type": "rank_position", "requirement_value": 1, "badge_color": "red", "display_order": 99},
    {"name": "Grand Master", "description": "Unlock 50 achievements", "icon": "fas fa-gem", "points": 200, "category": "special", "requirement_type": "achievement_percentage", "requirement_value": 50, "badge_color": "yellow", "display_order": 100}
]

app = create_app()

with app.app_context():
    print("=" * 60)
    print("SEEDING 100 ACHIEVEMENTS WITH ICONS")
    print("=" * 60)
    
    # Clear existing
    print("\n1. Clearing existing data...")
    db.session.execute(text('DELETE FROM user_achievement'))
    db.session.execute(text('DELETE FROM achievement'))
    db.session.commit()
    print("   ✓ Cleared")
    
    # Insert all 100 achievements
    print("\n2. Inserting 100 achievements...")
    for ach in ACHIEVEMENTS_100:
        achievement = Achievement(**ach)
        db.session.add(achievement)
    
    db.session.commit()
    print(f"   ✓ Inserted {len(ACHIEVEMENTS_100)} achievements")
    
    # Verify
    count = Achievement.query.count()
    print(f"\n3. Verification: {count} achievements in database")
    
    # Show some icons
    print("\n4. Sample icons:")
    sample = Achievement.query.filter(Achievement.name.in_(['Top 50', 'Top Performer', 'Weekend Warrior', 'Irrigation Specialist', 'Month Master', 'Year Round', 'Social Butterfly'])).all()
    for ach in sample:
        print(f"   ✓ {ach.name}: {ach.icon}")
    
    print("\n" + "=" * 60)
    print("✅ DONE! Restart Flask and refresh the page.")