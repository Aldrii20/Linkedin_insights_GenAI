import logging
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from config import config
from models import db, LinkedInPage, Post, Comment, Employee
from scraper import scrape_linkedin_page
from ai_summary import generate_summary
from utils import (
    extract_page_id_from_url,
    validate_url,
    paginate_list,
    format_response,
)


load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config_name: str = "development") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder="../frontend",
        static_url_path="/static",
        template_folder="../frontend",
    )

    
    app.config.from_object(config.get(config_name, config["development"]))

   
    db.init_app(app)
    CORS(app)

    
    with app.app_context():
        db.create_all()
        logger.info("    Database tables created/verified")

    
    register_routes(app)

    logger.info("=" * 50)
    logger.info("  LinkedIn Insights Server Started")
    logger.info("=" * 50)

    return app


def register_routes(app: Flask) -> None:
    """Register all API and static routes on the Flask app."""

    

    @app.route("/")
    def index():
        """Serve the main web UI."""
        return send_from_directory("../frontend", "index.html")

    @app.route("/static/<path:path>")
    def serve_static(path):
        """Serve static frontend assets."""
        return send_from_directory("../frontend", path)

   

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Basic health check endpoint."""
        return (
            jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0.0",
                }
            ),
            200,
        )

   

    @app.route("/api/pages", methods=["GET"])
    def get_pages():
        """Get pages with optional filters and pagination."""
        try:
            page_num = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)
            industry = request.args.get("industry", type=str)
            followers_min = request.args.get("followers_min", 0, type=int)
            followers_max = request.args.get("followers_max", None, type=int)

            query = LinkedInPage.query

            if industry:
                query = query.filter(
                    LinkedInPage.industry.ilike(f"%{industry}%")
                )

            if followers_min is not None and followers_min > 0:
                query = query.filter(
                    LinkedInPage.followers_count >= followers_min
                )

            if followers_max is not None:
                query = query.filter(
                    LinkedInPage.followers_count <= followers_max
                )

            pagination = query.paginate(
                page=page_num, per_page=per_page, error_out=False
            )

            data = {
                "pages": [p.to_dict() for p in pagination.items],
                "pagination": {
                    "total": pagination.total,
                    "page": page_num,
                    "per_page": per_page,
                    "total_pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }

            resp, code = format_response(
                True, data=data, message="Pages retrieved successfully", status_code=200
            )
            return jsonify(resp), code

        except Exception as exc:
            logger.exception("Error getting pages")
            resp, code = format_response(
                False, data=None, message=f"Error: {exc}", status_code=500
            )
            return jsonify(resp), code

    

    @app.route("/api/pages/<string:page_id>", methods=["GET"])
    def get_page(page_id: str):
        """Get a single page by ID."""
        try:
            include_posts = (
                request.args.get("include_posts", "true").lower() == "true"
            )
            include_employees = (
                request.args.get("include_employees", "true").lower() == "true"
            )

            page_obj = LinkedInPage.query.get(page_id)
            if not page_obj:
                resp, code = format_response(
                    False, None, "Page not found", status_code=404
                )
                return jsonify(resp), code

            data = page_obj.to_dict(
                include_posts=include_posts, include_employees=include_employees
            )
            resp, code = format_response(
                True, data=data, message="Page retrieved successfully", status_code=200
            )
            return jsonify(resp), code

        except Exception as exc:
            logger.exception("Error getting page %s", page_id)
            resp, code = format_response(
                False, None, f"Error: {exc}", status_code=500
            )
            return jsonify(resp), code

    

    @app.route("/api/pages/search", methods=["GET"])
    def search_pages():
        """Search pages by name with pagination."""
        try:
            query_str = request.args.get("q", "", type=str)
            page_num = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)

            if not query_str:
                resp, code = format_response(
                    False, None, "Search query required", status_code=400
                )
                return jsonify(resp), code

            pagination = LinkedInPage.query.filter(
                LinkedInPage.name.ilike(f"%{query_str}%")
            ).paginate(page=page_num, per_page=per_page, error_out=False)

            data = {
                "pages": [p.to_dict() for p in pagination.items],
                "pagination": {
                    "total": pagination.total,
                    "page": page_num,
                    "per_page": per_page,
                    "total_pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }

            resp, code = format_response(
                True, data=data, message="Search completed", status_code=200
            )
            return jsonify(resp), code

        except Exception as exc:
            logger.exception("Error searching pages")
            resp, code = format_response(
                False, None, f"Error: {exc}", status_code=500
            )
            return jsonify(resp), code

    

    @app.route("/api/scrape", methods=["POST"])
    def scrape_page():
        """Scrape a LinkedIn company page"""
        try:
            payload = request.get_json(silent=True) or {}
            url = (payload.get("url") or "").strip()
            force_rescrape = payload.get("force_rescrape", False)

            if not url:
                resp, code = format_response(False, None, "URL required", status_code=400)
                return jsonify(resp), code

            if not validate_url(url):
                resp, code = format_response(False, None, "Invalid LinkedIn URL", status_code=400)
                return jsonify(resp), code

            page_id = extract_page_id_from_url(url)
            if not page_id:
                resp, code = format_response(False, None, "Could not extract page ID", status_code=400)
                return jsonify(resp), code

            
            existing = db.session.get(LinkedInPage, page_id)
            
            if existing and force_rescrape:
                logger.info(f"🔄 Force re-scraping {page_id}")
                db.session.delete(existing)
                db.session.commit()
                existing = None
            
            if existing and not force_rescrape:
                logger.info(f"📦 Returning existing data for {page_id}")
                resp, code = format_response(
                    True,
                    data=existing.to_dict(include_posts=True, include_employees=True),
                    message="Page already in database",
                    status_code=200,
                )
                return jsonify(resp), code

            logger.info(f"🔍 Scraping: {page_id}")
            scraped = scrape_linkedin_page(page_id)

            if not scraped:
                resp, code = format_response(False, None, "Scraping failed", status_code=400)
                return jsonify(resp), code

            
            new_page = LinkedInPage(
                id=page_id,
                name=scraped.get("name", page_id),
                url=scraped.get("url", f"https://www.linkedin.com/company/{page_id}/"),
                profile_pic_url=scraped.get("profile_pic_url"),
                description=scraped.get("description"),
                website=scraped.get("website"),
                industry=scraped.get("industry"),
                followers_count=scraped.get("followers_count", 0),
                employees_count=scraped.get("employees_count", 0),
                employees_text=scraped.get("employees_text", ""),
                specialities=scraped.get("specialities"),
                last_scraped=datetime.utcnow(),
            )

           
            logger.info(f"📰 Adding {len(scraped.get('posts', []))} posts")
            for idx, post_data in enumerate(scraped.get("posts", [])[:25]):
                post = Post(
                    id=f"{page_id}_{post_data.get('id', f'post_{idx}')}",
                    page_id=page_id,
                    content=post_data.get("content"),
                    image_url=post_data.get("image_url"),
                    likes_count=post_data.get("likes_count", 0),
                    comments_count=post_data.get("comments_count", 0),
                    shares_count=post_data.get("shares_count", 0),
                )
                new_page.posts.append(post)

            
            logger.info(f"👥 Adding {len(scraped.get('employees', []))} employees")
            for idx, emp_data in enumerate(scraped.get("employees", [])[:50]):
                employee = Employee(
                    id=f"{page_id}_{emp_data.get('id', f'emp_{idx}')}",
                    page_id=page_id,
                    name=emp_data.get("name", "Unknown"),
                    headline=emp_data.get("headline"),
                    profile_url=emp_data.get("profile_url"),
                )
                new_page.employees.append(employee)

            db.session.add(new_page)
            db.session.commit()

            logger.info(f"  Saved {page_id} with {len(new_page.posts)} posts and {len(new_page.employees)} employees")

            result_data = new_page.to_dict(include_posts=True, include_employees=True)
            
            logger.info(f"📤 Returning data: posts={len(result_data.get('posts', []))}, employees={len(result_data.get('employees', []))}")

            resp, code = format_response(
                True,
                data=result_data,
                message="Page scraped successfully",
                status_code=201,
            )
            return jsonify(resp), code

        except Exception as exc:
            db.session.rollback()
            logger.exception("Scrape error")
            resp, code = format_response(False, None, f"Error: {exc}", status_code=500)
            return jsonify(resp), code

    

    @app.route("/api/pages/<string:page_id>/summary", methods=["GET"])
    def get_ai_summary(page_id: str):
        """Generate or retrieve AI summary for a page"""
        try:
            page_obj = db.session.get(LinkedInPage, page_id)
            if not page_obj:
                resp, code = format_response(
                    False, None, "Page not found", status_code=404
                )
                return jsonify(resp), code

            # If summary already exists, return it
            if page_obj.ai_summary:
                logger.info(f"📝 Returning existing summary for {page_id}")
                resp, code = format_response(
                    True,
                    data={"summary": page_obj.ai_summary},
                    message="Summary retrieved",
                    status_code=200,
                )
                return jsonify(resp), code

          
            logger.info(f"     Generating AI summary for {page_id}")
            
            import os
            groq_api_key = os.environ.get('GROQ_API_KEY', app.config.get('GROQ_API_KEY', ''))
            
            page_data = page_obj.to_dict(include_posts=True, include_employees=True)
            summary = generate_summary(page_data, api_key=groq_api_key)
            
            
            page_obj.ai_summary = summary
            db.session.commit()
            
            logger.info(f"  Summary generated and saved for {page_id}")
            
            resp, code = format_response(
                True,
                data={"summary": summary},
                message="Summary generated successfully",
                status_code=200,
            )
            return jsonify(resp), code

        except Exception as exc:
            logger.exception("Error generating summary")
            resp, code = format_response(
                False, None, f"Error: {exc}", status_code=500
            )
            return jsonify(resp), code

    

    @app.route("/api/pages/<string:page_id>/export", methods=["GET"])
    def export_page_json(page_id: str):
        """Export complete page insights as JSON file"""
        try:
            page_obj = db.session.get(LinkedInPage, page_id)
            if not page_obj:
                resp, code = format_response(
                    False, None, "Page not found", status_code=404
                )
                return jsonify(resp), code

            export_data = {
                "export_info": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "page_id": page_id,
                    "source": "LinkedIn Insights Microservice",
                },
                "company_profile": {
                    "name": page_obj.name,
                    "url": page_obj.url,
                    "industry": page_obj.industry,
                    "followers_count": page_obj.followers_count,
                    "employees_count": page_obj.employees_count,
                    "description": page_obj.description,
                    "website": page_obj.website,
                    "specialities": page_obj.specialities,
                    "profile_picture_url": page_obj.profile_pic_url,
                },
                "ai_insights": {
                    "summary": page_obj.ai_summary,
                    "key_metrics": {
                        "total_followers": page_obj.followers_count,
                        "total_posts": len(page_obj.posts),
                        "total_employees_found": len(page_obj.employees),
                        "engagement_score": sum([p.likes_count + p.comments_count for p in page_obj.posts]),
                    }
                },
                "posts": [
                    {
                        "id": post.id,
                        "content": post.content,
                        "likes": post.likes_count,
                        "comments": post.comments_count,
                        "shares": post.shares_count,
                        "posted_date": post.posted_date.isoformat() if post.posted_date else None,
                    }
                    for post in page_obj.posts
                ],
                "employees": [
                    {
                        "name": emp.name,
                        "headline": emp.headline,
                        "profile_url": emp.profile_url,
                    }
                    for emp in page_obj.employees
                ],
                "metadata": {
                    "last_scraped": page_obj.last_scraped.isoformat() if page_obj.last_scraped else None,
                    "created_at": page_obj.created_at.isoformat() if page_obj.created_at else None,
                }
            }

            from flask import Response
            import json
            
            response = Response(
                json.dumps(export_data, indent=2, ensure_ascii=False),
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename={page_id}_insights.json'
                }
            )
            
            logger.info(f"📥 JSON export generated for {page_id}")
            return response

        except Exception as exc:
            logger.exception("Error exporting page to JSON")
            resp, code = format_response(
                False, None, f"Error: {exc}", status_code=500
            )
            return jsonify(resp), code

    

    @app.errorhandler(404)
    def not_found(_error):
        resp, code = format_response(
            False, None, "Endpoint not found", status_code=404
        )
        return jsonify(resp), code

    @app.errorhandler(500)
    def internal_error(error):
        logger.exception("Internal server error: %s", error)
        resp, code = format_response(
            False, None, "Internal server error", status_code=500
        )
        return jsonify(resp), code


if __name__ == "__main__":
    app = create_app("development")
    logger.info("   Server running on http://localhost:5000")
    logger.info("   Frontend: http://localhost:5000/")
    app.run(host="0.0.0.0", port=5000, debug=True)
