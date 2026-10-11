from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from api.models import Project, ProjectFile, UserFeedback, Notification, ShowcaseItem
from api import signals

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds 10 realistic demo users, projects, feedbacks, and showcase items with before/after images."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo users, projects, feedbacks, and showcase items...")

        # Temporarily disconnect signals to prevent external SMTP emails during batch seeding
        post_save.disconnect(signals.send_user_creation_notification, sender=User)
        post_save.disconnect(signals.send_project_upload_notification, sender=ProjectFile)
        post_save.disconnect(signals.send_user_feedback_notification, sender=UserFeedback)
        post_save.disconnect(signals.send_feedback_approved_notification, sender=UserFeedback)

        demo_data = [
            {
                "email": "alex.morgan@cadverse-demo.io",
                "name": "Alex Morgan",
                "mobile": "+1 (555) 234-5678",
                "project": {
                    "name": "Titanium Aerospace Bracket",
                    "description": "Topology-optimized aerospace mounting bracket with 35% weight reduction.",
                    "type": "3D Model Design",
                    "status": "Completed",
                    "files": ["bracket_v3_optimized.step", "fea_stress_analysis.pdf"],
                    "feedback": {
                        "rating": 5,
                        "text": "Exceptional precision! The FEA stress report and STEP files were flawless.",
                        "emojis": "🚀 ✈️ 🔥",
                        "status": "approved",
                        "short_note": "High-priority aerospace client, approved for showcase."
                    },
                    "showcase": {
                        "title": "Titanium Aerospace Bracket - Generative Topology Optimization",
                        "before_url": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1581092335397-9583fe92d232?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "priya.sharma@cadverse-demo.io",
                "name": "Priya Sharma",
                "mobile": "+91 98765 43210",
                "project": {
                    "name": "Custom Quadcopter Drone Chassis",
                    "description": "Carbon fiber reinforced drone chassis designed for agricultural multispectral imaging.",
                    "type": "3D Printing",
                    "status": "Completed",
                    "files": ["drone_chassis_frame.stl", "motor_mount_specs.pdf"],
                    "feedback": {
                        "rating": 5,
                        "text": "The test print fit perfectly with the motors. The carbon fiber nylon finish is super durable.",
                        "emojis": "🚁 🌾 ⭐",
                        "status": "approved",
                        "short_note": "Agricultural drone showcase partner."
                    },
                    "showcase": {
                        "title": "Agricultural Drone Chassis - Carbon Composite 3D Print",
                        "before_url": "https://images.unsplash.com/photo-1508614589041-895b88991e3e?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1527977966376-1c8408f9f108?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "marcus.vance@cadverse-demo.io",
                "name": "Marcus Vance",
                "mobile": "+44 20 7946 0912",
                "project": {
                    "name": "Automotive Suspension Wishbone FEA",
                    "description": "Dynamic load simulation and fatigue analysis for Formula Student double wishbone suspension.",
                    "type": "Simulation",
                    "status": "Completed",
                    "files": ["wishbone_fatigue_sim.iges", "safety_factor_report.pdf"],
                    "feedback": {
                        "rating": 5,
                        "text": "Comprehensive analysis report! Helped our university team pass technical inspection with flying colors.",
                        "emojis": "🏎️ ⚡ 🛠️",
                        "status": "approved",
                        "short_note": "Formula Student sponsorship partner."
                    },
                    "showcase": {
                        "title": "Formula Suspension Wishbone - High-G Dynamic Load FEA",
                        "before_url": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "elena.rostova@cadverse-demo.io",
                "name": "Elena Rostova",
                "mobile": "+49 30 1234567",
                "project": {
                    "name": "Bionic Prosthetic Hand Mechanism",
                    "description": "Underactuated compliant mechanism design for lightweight pediatric prosthetic hand.",
                    "type": "3D Model Design",
                    "status": "Completed",
                    "files": ["prosthetic_finger_assembly.sldasm", "tendon_routing.pdf"],
                    "feedback": {
                        "rating": 5,
                        "text": "The natural grip ergonomics and tendon path designs are truly state of the art.",
                        "emojis": "🦾 ❤️ 💡",
                        "status": "approved",
                        "short_note": "Medical robotics collaboration."
                    },
                    "showcase": {
                        "title": "Bionic Prosthetic Hand - Compliant Tendon-Driven Assembly",
                        "before_url": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "david.kim@cadverse-demo.io",
                "name": "David Kim",
                "mobile": "+82 2 3456 7890",
                "project": {
                    "name": "Liquid Cooling Cold Plate for EV Battery",
                    "description": "Computational Fluid Dynamics (CFD) simulation of serpentine microchannel liquid cooling.",
                    "type": "Simulation",
                    "status": "Completed",
                    "files": ["cooling_plate_cfd_mesh.step", "thermal_distribution_map.png"],
                    "feedback": {
                        "rating": 5,
                        "text": "Thermal gradient dropped by 14°C across battery pack. CFD validation was spot on!",
                        "emojis": "🔋 ❄️ ⚡",
                        "status": "approved",
                        "short_note": "EV battery pack thermal management."
                    },
                    "showcase": {
                        "title": "EV Battery Cold Plate - Microchannel CFD Thermal Optimization",
                        "before_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "sophia.chen@cadverse-demo.io",
                "name": "Sophia Chen",
                "mobile": "+1 (415) 876-5432",
                "project": {
                    "name": "Architectural Parametric Facade Panels",
                    "description": "Generative voronoi facade shading system for LEED-certified commercial tower.",
                    "type": "3D Model Design",
                    "status": "Completed",
                    "files": ["facade_voronoi_panel_01.dwg", "sun_exposure_study.pdf"],
                    "feedback": {
                        "rating": 4,
                        "text": "Beautiful parametric detailing and very clean curvature continuity across panel seams.",
                        "emojis": "🏢 ☀️ 📐",
                        "status": "approved",
                        "short_note": "Architectural facade showcase."
                    },
                    "showcase": {
                        "title": "LEED Commercial Tower - Parametric Voronoi Solar Shading Facade",
                        "before_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "liam.oconnor@cadverse-demo.io",
                "name": "Liam O'Connor",
                "mobile": "+353 1 496 0123",
                "project": {
                    "name": "Industrial Robotic End-Effector Gripper",
                    "description": "High-torque pneumatic parallel gripper with quick-change mounting interface.",
                    "type": "3D Model Design",
                    "status": "Completed",
                    "files": ["gripper_cad_model.step", "pneumatic_schematic.pdf"],
                    "feedback": {
                        "rating": 5,
                        "text": "Payload capacity increased by 25% while reducing overall assembly weight.",
                        "emojis": "🤖 🔧 🦾",
                        "status": "approved",
                        "short_note": "Industrial automation gripper."
                    },
                    "showcase": {
                        "title": "Industrial Robotic End-Effector - Adaptive Pneumatic Gripper",
                        "before_url": "https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "amara.diop@cadverse-demo.io",
                "name": "Amara Diop",
                "mobile": "+33 1 42 68 55 00",
                "project": {
                    "name": "Hydrofoil Surfboard Mast & Wing Assembly",
                    "description": "High-modulus carbon hydrofoil wing profile optimized for low-speed takeoff.",
                    "type": "Simulation",
                    "status": "Completed",
                    "files": ["foil_hydrodynamics_v2.step", "lift_drag_polar.csv"],
                    "feedback": {
                        "rating": 5,
                        "text": "Remarkable hydrofoil balance. Hydrodynamic drag was cut down by 18%!",
                        "emojis": "🏄‍♂️ 🌊 💨",
                        "status": "approved",
                        "short_note": "Water sports engineering."
                    },
                    "showcase": {
                        "title": "Carbon Hydrofoil Wing - Hydrodynamic Low-Speed Foil Profile",
                        "before_url": "https://images.unsplash.com/photo-1502680390469-be75c86b636f?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "karthik.ramesh@cadverse-demo.io",
                "name": "Karthik Ramesh",
                "mobile": "+91 99887 76655",
                "project": {
                    "name": "Centrifugal Pump Impeller Optimization",
                    "description": "Cavitation suppression and blade curvature optimization for slurry transport pump.",
                    "type": "3D Model Design",
                    "status": "Completed",
                    "files": ["impeller_5blade_opt.step", "cavitation_risk_map.pdf"],
                    "feedback": {
                        "rating": 5,
                        "text": "Zero cavitation observed in physical trials! Great hydraulic performance.",
                        "emojis": "💧 ⚙️ 📈",
                        "status": "approved",
                        "short_note": "Industrial fluid machinery."
                    },
                    "showcase": {
                        "title": "Slurry Centrifugal Pump - 5-Blade Anti-Cavitation Impeller",
                        "before_url": "https://images.unsplash.com/photo-1581092162384-8987c1d64718?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1581092795360-fd1ca04f0952?auto=format&fit=crop&w=800&q=80"
                    }
                }
            },
            {
                "email": "natalie.brooks@cadverse-demo.io",
                "name": "Natalie Brooks",
                "mobile": "+1 (617) 555-0199",
                "project": {
                    "name": "Surgical Bone Drill Ergonomic Housing",
                    "description": "Autoclavable ergonomic medical housing with internal motor vibration damping.",
                    "type": "3D Printing",
                    "status": "Completed",
                    "files": ["surgical_housing_biocompatible.stl", "autoclave_specs.pdf"],
                    "feedback": {
                        "rating": 5,
                        "text": "Surgeon hand fatigue reduced drastically in clinical simulation tests.",
                        "emojis": "🩺 🏥 💉",
                        "status": "approved",
                        "short_note": "Medical orthopedic instrument."
                    },
                    "showcase": {
                        "title": "Surgical Orthopedic Drill - Autoclavable PEEK Ergonomic Housing",
                        "before_url": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=800&q=80",
                        "after_url": "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?auto=format&fit=crop&w=800&q=80"
                    }
                }
            }
        ]

        created_feedback_count = 0
        created_showcase_count = 0

        for item in demo_data:
            user, _ = User.objects.get_or_create(
                email=item["email"],
                defaults={
                    "name": item["name"],
                    "mobile": item["mobile"],
                    "is_verified": True,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                }
            )

            pdata = item["project"]
            project, _ = Project.objects.get_or_create(
                user=user,
                name=pdata["name"],
                defaults={
                    "description": pdata["description"],
                    "type": pdata["type"],
                    "status": pdata["status"],
                }
            )
            # Ensure status is updated to completed
            project.status = pdata["status"]
            project.description = pdata["description"]
            project.save()

            # Files
            for fname in pdata.get("files", []):
                ProjectFile.objects.get_or_create(
                    project=project,
                    file_name=fname,
                    defaults={
                        "file_url": f"https://udrpuywfjwiprcfumvcs.supabase.co/storage/v1/object/public/cadverse-files/{user.email}/{fname}"
                    }
                )

            # Feedback
            fb_info = pdata["feedback"]
            feedback, fb_created = UserFeedback.objects.get_or_create(
                user=user,
                project=project,
                defaults={
                    "rating": fb_info["rating"],
                    "feedback_text": fb_info["text"],
                    "emojis": fb_info["emojis"],
                    "status": fb_info["status"],
                    "is_approved": True,
                    "short_note": fb_info["short_note"],
                    "popup_count": 1
                }
            )
            if not fb_created:
                feedback.rating = fb_info["rating"]
                feedback.feedback_text = fb_info["text"]
                feedback.emojis = fb_info["emojis"]
                feedback.status = fb_info["status"]
                feedback.is_approved = True
                feedback.short_note = fb_info["short_note"]
                feedback.save()
            created_feedback_count += 1

            # Showcase Item
            sc_info = pdata["showcase"]
            showcase, sc_created = ShowcaseItem.objects.get_or_create(
                feedback=feedback,
                defaults={
                    "title": sc_info["title"],
                    "before_url": sc_info["before_url"],
                    "after_url": sc_info["after_url"]
                }
            )
            if not sc_created:
                showcase.title = sc_info["title"]
                showcase.before_url = sc_info["before_url"]
                showcase.after_url = sc_info["after_url"]
                showcase.save()
            created_showcase_count += 1

        # Reconnect signals
        post_save.connect(signals.send_user_creation_notification, sender=User)
        post_save.connect(signals.send_project_upload_notification, sender=ProjectFile)
        post_save.connect(signals.send_user_feedback_notification, sender=UserFeedback)
        post_save.connect(signals.send_feedback_approved_notification, sender=UserFeedback)

        self.stdout.write(self.style.SUCCESS(
            f"[OK] Successfully seeded {created_feedback_count} Feedbacks and {created_showcase_count} Showcase Items with Before & After images!"
        ))
