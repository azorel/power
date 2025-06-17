/**
 * Power Builder - Main JavaScript for Enhanced Glassmorphism Interactions
 * Provides smooth animations, responsive behavior, and enhanced user experience
 */

class PowerBuilderApp {
  constructor() {
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.setupScrollEffects();
    this.setupAnimations();
    this.setupResponsiveNavigation();
    this.setupGlassEffects();
  }

  setupEventListeners() {
    try {
      // Smooth scrolling for navigation links
      document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", (e) => {
          try {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute("href"));
            if (target) {
              target.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });
            }
          } catch (error) {
            console.error("Error in smooth scroll handler:", error);
          }
        });
      });
    } catch (error) {
      console.error("Error setting up event listeners:", error);
    }

    // Enhanced button interactions
    document.querySelectorAll(".glass-btn").forEach((button) => {
      button.addEventListener("mouseenter", this.handleButtonHover.bind(this));
      button.addEventListener("mouseleave", this.handleButtonLeave.bind(this));
      button.addEventListener("click", this.handleButtonClick.bind(this));
    });

    // Intersection Observer for scroll animations
    this.setupIntersectionObserver();
  }

  setupScrollEffects() {
    let lastScrollY = window.scrollY;

    window.addEventListener("scroll", () => {
      const currentScrollY = window.scrollY;
      const navElement = document.querySelector(".glass-nav");

      // Enhanced dynamic navigation glass effect based on scroll
      if (currentScrollY > 50) {
        navElement.style.background = "rgba(255, 255, 255, 0.08)";
        navElement.style.backdropFilter = "blur(60px) saturate(200%)";
        navElement.style.boxShadow =
          "0 12px 40px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.12)";
      } else {
        navElement.style.background = "rgba(255, 255, 255, 0.06)";
        navElement.style.backdropFilter = "blur(50px) saturate(200%)";
        navElement.style.boxShadow =
          "0 8px 32px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1)";
      }

      // Background is now static - no parallax movement

      lastScrollY = currentScrollY;
    });
  }

  setupAnimations() {
    // Staggered animation for cards
    const cards = document.querySelectorAll(".glass-card, .glass-mini-card");
    cards.forEach((card, index) => {
      card.style.animationDelay = `${index * 0.1}s`;
    });

    // Floating animation for feature icons
    const featureIcons = document.querySelectorAll(".feature-icon");
    featureIcons.forEach((icon) => {
      icon.addEventListener("mouseenter", () => {
        icon.style.transform = "scale(1.2) rotate(10deg)";
        icon.style.transition = "transform 0.3s ease-out";
      });

      icon.addEventListener("mouseleave", () => {
        icon.style.transform = "scale(1) rotate(0deg)";
      });
    });
  }

  setupResponsiveNavigation() {
    // Mobile menu toggle functionality
    const navMenu = document.querySelector(".nav-menu");
    const navBrand = document.querySelector(".nav-brand");

    // Create mobile menu toggle button
    const mobileToggle = document.createElement("button");
    mobileToggle.className = "mobile-menu-toggle";
    mobileToggle.innerHTML = "☰";
    mobileToggle.style.cssText = `
            display: none;
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.5rem;
        `;

    navBrand.appendChild(mobileToggle);

    // Handle mobile menu toggle
    mobileToggle.addEventListener("click", () => {
      navMenu.classList.toggle("mobile-active");
      mobileToggle.innerHTML = navMenu.classList.contains("mobile-active")
        ? "✕"
        : "☰";
    });

    // Handle window resize
    window.addEventListener("resize", () => {
      if (window.innerWidth > 768) {
        navMenu.classList.remove("mobile-active");
        mobileToggle.innerHTML = "☰";
      }
    });

    // Add mobile styles
    this.addMobileStyles();
  }

  addMobileStyles() {
    const style = document.createElement("style");
    style.textContent = `
            @media (max-width: 768px) {
                .mobile-menu-toggle {
                    display: block !important;
                }
                
                .nav-menu {
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(25px);
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    flex-direction: column;
                    padding: 1rem;
                    transform: translateY(-100%);
                    opacity: 0;
                    visibility: hidden;
                    transition: all 0.3s ease;
                }
                
                .nav-menu.mobile-active {
                    transform: translateY(0);
                    opacity: 1;
                    visibility: visible;
                }
                
                .nav-menu li {
                    margin: 0.5rem 0;
                }
            }
        `;
    document.head.appendChild(style);
  }

  setupGlassEffects() {
    // Enhanced glass morphism effects on hover
    document.querySelectorAll(".glass-mini-card").forEach((card) => {
      card.addEventListener("mouseenter", (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        card.style.setProperty("--mouse-x", `${x}px`);
        card.style.setProperty("--mouse-y", `${y}px`);

        // Add subtle glow effect
        card.style.boxShadow = `
                    0 8px 24px rgba(0, 0, 0, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.12),
                    0 0 20px rgba(255, 255, 255, 0.1)
                `;
      });

      card.addEventListener("mouseleave", () => {
        card.style.boxShadow = `
                    0 4px 16px rgba(0, 0, 0, 0.05),
                    inset 0 1px 0 rgba(255, 255, 255, 0.08)
                `;
      });
    });
  }

  setupIntersectionObserver() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-in");
        }
      });
    }, observerOptions);

    // Observe all sections
    document.querySelectorAll("section").forEach((section) => {
      observer.observe(section);
    });

    // Add animation styles
    const animationStyle = document.createElement("style");
    animationStyle.textContent = `
            section {
                opacity: 0;
                transform: translateY(30px);
                transition: all 0.6s ease-out;
            }
            
            section.animate-in {
                opacity: 1;
                transform: translateY(0);
            }
        `;
    document.head.appendChild(animationStyle);
  }

  handleButtonHover(e) {
    const button = e.target;
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Create ripple effect
    const ripple = document.createElement("div");
    ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: scale(0);
            animation: ripple 0.6s linear;
            left: ${x}px;
            top: ${y}px;
            width: 20px;
            height: 20px;
            margin-left: -10px;
            margin-top: -10px;
            pointer-events: none;
        `;

    button.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, 600);
  }

  handleButtonLeave(e) {
    // Button leave animation handled by CSS
  }

  handleButtonClick(e) {
    const button = e.target;

    // Add click animation
    button.style.transform = "scale(0.95)";
    setTimeout(() => {
      button.style.transform = "";
    }, 150);

    // Handle specific button actions
    if (button.textContent.includes("Start Building")) {
      this.handleStartBuilding();
    } else if (button.textContent.includes("Documentation")) {
      this.handleViewDocumentation();
    }
  }

  handleStartBuilding() {
    // Placeholder for start building action
    console.log("Starting Power Builder...");
    // Could redirect to setup page or show modal
  }

  handleViewDocumentation() {
    // Placeholder for documentation action
    console.log("Opening documentation...");
    // Could redirect to docs or show inline help
  }

  // Utility methods for enhanced effects
  addRippleEffect() {
    const rippleStyle = document.createElement("style");
    rippleStyle.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
    document.head.appendChild(rippleStyle);
  }

  // Performance optimization
  throttle(func, limit) {
    let inThrottle;
    return function () {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }
}

// Initialize the application when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new PowerBuilderApp();
});

// Export for testing
if (typeof module !== "undefined" && module.exports) {
  module.exports = PowerBuilderApp;
}
