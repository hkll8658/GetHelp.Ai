<?php
include 'config.php';

// Check if user is logged in
if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit();
}

// Get user info
$user_id = $_SESSION['user_id'];
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$user_id]);
$user = $stmt->fetch();

// Get user's average rating
$stmt = $pdo->prepare("SELECT AVG(rating) as avg_rating FROM star_ratings WHERE user_id = ?");
$stmt->execute([$user_id]);
$rating_data = $stmt->fetch();
$user_rating = $rating_data['avg_rating'] ? round($rating_data['avg_rating']) : 0;

// Get products
$stmt = $pdo->prepare("SELECT * FROM products WHERE status = 'active'");
$stmt->execute();
$products = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BGMI Loader - Premium BGMI Services</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;500;700&display=swap">
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #ff5722;
            --primary-dark: #e64a19;
            --secondary: #2196f3;
            --dark: #121212;
            --darker: #0a0a0a;
            --light: #f5f5f5;
            --gray: #2a2a2a;
            --success: #4caf50;
        }

        body {
            font-family: 'Roboto', sans-serif;
            background: linear-gradient(135deg, var(--darker), #1a1a2e);
            color: var(--light);
            line-height: 1.6;
            overflow-x: hidden;
            min-height: 100vh;
            background-attachment: fixed;
        }

        /* Header Styles */
        header {
            background-color: rgba(10, 10, 10, 0.9);
            backdrop-filter: blur(10px);
            padding: 15px 5%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            border-bottom: 2px solid var(--primary);
        }

        .logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8rem;
            color: var(--primary);
            text-shadow: 0 0 10px rgba(255, 87, 34, 0.7);
            letter-spacing: 1px;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-right: 20px;
        }

        .user-name {
            font-weight: 500;
        }

        .user-rating {
            color: #ffc107;
        }

        .menu-btn {
            background: var(--primary);
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .menu-btn:hover {
            background: var(--primary-dark);
            transform: scale(1.05);
        }

        .menu-btn span {
            display: block;
            width: 25px;
            height: 3px;
            background: white;
            margin: 2px 0;
            border-radius: 2px;
            transition: all 0.3s ease;
        }

        /* Side Navigation */
        .side-nav {
            position: fixed;
            top: 0;
            right: -300px;
            width: 280px;
            height: 100%;
            background: var(--dark);
            z-index: 1001;
            padding: 80px 20px 20px;
            transition: right 0.4s ease;
            box-shadow: -5px 0 15px rgba(0, 0, 0, 0.5);
            overflow-y: auto;
        }

        .side-nav.active {
            right: 0;
        }

        .nav-close {
            position: absolute;
            top: 20px;
            right: 20px;
            background: var(--primary);
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            color: white;
            font-size: 1.2rem;
        }

        .nav-list {
            list-style: none;
        }

        .nav-list li {
            margin-bottom: 15px;
        }

        .nav-list a {
            display: block;
            padding: 12px 15px;
            background: var(--gray);
            border-radius: 8px;
            color: white;
            text-decoration: none;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
        }

        .nav-list a:hover, .nav-list a.active {
            background: var(--primary);
            border-left: 4px solid white;
            transform: translateX(5px);
        }

        /* Logout Section */
        .logout-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #444;
        }

        .logout-section a {
            display: block;
            padding: 12px 15px;
            background: #f44336;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .logout-section a:hover {
            background: #d32f2f;
            transform: translateY(-2px);
        }

        /* Main Content */
        main {
            padding: 100px 5% 50px;
            min-height: 100vh;
        }

        .page {
            display: none;
            animation: fadeIn 0.5s ease;
        }

        .page.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Home Page */
        .hero {
            text-align: center;
            padding: 40px 0;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
            border-radius: 15px;
            background: rgba(33, 33, 33, 0.6);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 87, 34, 0.3);
        }

        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('images/xyz/xyz0.jpg') center/cover no-repeat;
            opacity: 0.3;
            z-index: -1;
        }

        .hero h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 3.5rem;
            margin-bottom: 20px;
            color: var(--primary);
            text-shadow: 0 0 15px rgba(255, 87, 34, 0.8);
        }

        .hero p {
            font-size: 1.2rem;
            max-width: 800px;
            margin: 0 auto 30px;
            color: #e0e0e0;
        }

        .emoji {
            font-size: 1.5rem;
            margin: 0 5px;
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 50px 0;
        }

        .feature-card {
            background: rgba(42, 42, 42, 0.7);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            transition: transform 0.3s ease;
            border: 1px solid rgba(255, 87, 34, 0.2);
        }

        .feature-card:hover {
            transform: translateY(-10px);
            border-color: var(--primary);
        }

        .feature-card i {
            font-size: 3rem;
            color: var(--primary);
            margin-bottom: 20px;
        }

        .feature-card h3 {
            font-size: 1.5rem;
            margin-bottom: 15px;
        }

        /* Products */
        .products {
            margin: 50px 0;
        }

        .section-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.2rem;
            text-align: center;
            margin-bottom: 40px;
            color: var(--primary);
            position: relative;
        }

        .section-title::after {
            content: '';
            display: block;
            width: 80px;
            height: 4px;
            background: var(--primary);
            margin: 10px auto;
            border-radius: 2px;
        }

        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
        }

        .product-card {
            background: rgba(33, 33, 33, 0.8);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .product-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 12px 25px rgba(255, 87, 34, 0.3);
            border-color: var(--primary);
        }
        
        .product-img {
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }

        .product-img img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }

        .product-card:hover .product-img img {
            transform: scale(1.05);
        }

        .product-content {
            padding: 20px;
        }

        .product-title {
            font-size: 1.4rem;
            margin-bottom: 10px;
            color: var(--primary);
        }

        .product-desc {
            color: #bdbdbd;
            margin-bottom: 15px;
            min-height: 80px;
        }

        .product-meta {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            background: rgba(0, 0, 0, 0.3);
            padding: 10px;
            border-radius: 8px;
        }

        .product-balance, .product-price {
            font-weight: 700;
        }

        .product-price {
            color: var(--primary);
            font-size: 1.3rem;
        }

        .buy-btn {
            display: block;
            width: 100%;
            padding: 12px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            text-decoration: none;
        }

        .buy-btn:hover {
            background: var(--primary-dark);
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(255, 87, 34, 0.4);
        }

        .buy-btn:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        /* Quick Links */
        .quick-links {
            margin: 50px 0;
            text-align: center;
        }

        .links-container {
            display: flex;
            justify-content: center;
            gap: 25px;
            flex-wrap: wrap;
            margin-top: 30px;
        }

        .link-btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 120px;
            text-decoration: none;
            color: white;
            transition: all 0.3s ease;
        }

        .link-btn:hover {
            transform: translateY(-8px);
        }

        .link-icon {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            margin-bottom: 10px;
        }

        .youtube { background: #ff0000; }
        .instagram { background: #e1306c; }
        .telegram { background: #0088cc; }
        .support { background: var(--success); }

        .link-label {
            font-size: 0.9rem;
        }

        /* Footer */
        footer {
            background: var(--darker);
            padding: 30px 5%;
            text-align: center;
            border-top: 2px solid var(--primary);
        }

        .footer-content {
            max-width: 500px;
            margin: 0 auto;
        }

        .footer-logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            color: var(--primary);
            margin-bottom: 20px;
        }

        .copyright {
            color: #aaa;
            font-size: 0.9rem;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }

        .modal.active {
            display: flex;
            animation: fadeIn 0.3s ease;
        }

        .modal-content {
            background: var(--dark);
            width: 90%;
            max-width: 500px;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 0 30px rgba(255, 87, 34, 0.5);
            position: relative;
        }

        .modal-header {
            background: var(--primary);
            padding: 20px;
            text-align: center;
        }

        .modal-header h2 {
            font-family: 'Orbitron', sans-serif;
        }

        .modal-close {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0, 0, 0, 0.3);
            color: white;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 1.2rem;
        }

        .modal-body {
            padding: 25px;
            text-align: center;
        }

        .modal-img {
            max-width: 250px;
            margin: 0 auto 20px;
            background: white;
            padding: 15px;
            border-radius: 10px;
        }

        .modal-img img {
            width: 100%;
            display: block;  
        }   

        .modal-details {
            margin-bottom: 20px;
        }

        .modal-price {
            font-size: 1.8rem;
            color: var(--primary);
            font-weight: 700;
            margin: 10px 0;
        }

        .modal-note {
            background: rgba(255, 87, 34, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 0.9rem;
        }

        .telegram-link {
            color: #0088cc;
            text-decoration: none;
            font-weight: 700;
        }

        /* About Page */
        .about-content {
            max-width: 800px;
            margin: 0 auto;
        }

        .about-section {
            background: rgba(33, 33, 33, 0.7);
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
            border-left: 4px solid var(--primary);
        }

        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }

        .gallery img {
            width: 100%;
            border-radius: 10px;
            aspect-ratio: 1/1;
            object-fit: cover;
            border: 2px solid var(--primary);
        }

        /* Feedback Page */
        .feedback-content {
            max-width: 1000px;
            margin: 0 auto;
        }

        .media-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }

        .media-item {
            border-radius: 10px;
            overflow: hidden;
            aspect-ratio: 1/1;
            background: linear-gradient(45deg, #ff8a00, #e52e71);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
        }

        .media-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .rating-section {
            background: rgba(33, 33, 33, 0.7);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin: 40px 0;
        }

        .stars {
            font-size: 2.5rem;
            margin: 20px 0;
            color: #ffc107;
        }

        .stars i {
            margin: 0 5px;
            cursor: pointer;
            transition: transform 0.2s ease;
        }

        .stars i:hover {
            transform: scale(1.2);
        }

        /* Support Page */
        .support-content {
            max-width: 800px;
            margin: 0 auto;
        }

        .support-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 25px;
            margin: 40px 0;
        }

        .support-card {
            background: rgba(33, 33, 33, 0.7);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .support-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 10px 25px rgba(255, 87, 34, 0.3);
        }

        .support-icon {
            font-size: 3rem;
            margin-bottom: 20px;
        }

        .instagram-icon { color: #e1306c; }
        .telegram-icon { color: #0088cc; }
        .youtube-icon { color: #ff0000; }

        .support-btn {
            display: inline-block;
            margin-top: 15px;
            padding: 10px 20px;
            background: var(--primary);
            color: white;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 700;
            transition: all 0.3s ease;
        }

        .support-btn:hover {
            background: var(--primary-dark);
            transform: scale(1.05);
        }

        /* User Rating Section */
        .user-rating-section {
            background: rgba(33, 33, 33, 0.7);
            padding: 25px;
            border-radius: 12px;
            margin: 30px 0;
            border-left: 4px solid #ffc107;
        }

        .rating-history {
            margin-top: 20px;
        }

        .rating-item {
            background: rgba(42, 42, 42, 0.7);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .rating-stars {
            margin-bottom: 10px;
        }

        .rating-meta {
            font-size: 0.9rem;
            color: #bdbdbd;
            margin-bottom: 5px;
        }

        .rating-comment {
            font-style: italic;
            color: #e0e0e0;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .hero h1 {
                font-size: 2.5rem;
            }
            
            .section-title {
                font-size: 1.8rem;
            }
            
            .modal-content {
                width: 95%;
            }
            
            .user-info {
                display: none;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header>
        <div class="logo">BGMI LOADER</div>
        <div class="user-info">
            <span class="user-name">Welcome, <?php echo htmlspecialchars($user['username']); ?></span>
            <div class="user-rating">
                <?php for ($i = 1; $i <= 5; $i++): ?>
                    <i class="<?php echo $i <= $user_rating ? 'fas' : 'far'; ?> fa-star"></i>
                <?php endfor; ?>
            </div>
        </div>
        <button class="menu-btn" id="menuBtn">
            <span></span>
            <span></span>
            <span></span>
        </button>
    </header>

    <!-- Side Navigation -->
    <div class="side-nav" id="sideNav">
        <div class="nav-close" id="navClose">
            <i class="fas fa-times"></i>
        </div>
        <ul class="nav-list">
            <li><a href="#" class="nav-link active" data-page="home">Home</a></li>
            <li><a href="#" class="nav-link" data-page="survive">Survive</a></li>
            <li><a href="#" class="nav-link" data-page="about">About</a></li>
            <li><a href="#" class="nav-link" data-page="feedback">Feedback</a></li>
            <li><a href="#" class="nav-link" data-page="support">Support</a></li>
        </ul>
        
        <!-- Logout Section -->
        <div class="logout-section">
            <a href="logout.php">
                <i class="fas fa-sign-out-alt"></i> Logout
            </a>
        </div>
    </div>

    <!-- Main Content -->
    <main>
        <!-- Home Page -->
        <div class="page active" id="home">
            <section class="hero">
                <h1>WELCOME TO BGMI LOADER</h1>
                <p>
                    Experience BGMI like never before! 🎮 Our premium hacks and mods give you the ultimate advantage. 
                    Dominate the battlefield with enhanced features and become the last man standing! 🔥
                </p>
            </section>

            <!-- User Rating Section -->
            <section class="user-rating-section">
                <h3>Your Rating: <?php echo number_format($user_rating, 1); ?>/5.0</h3>
                <div class="stars">
                    <?php for ($i = 1; $i <= 5; $i++): ?>
                        <i class="<?php echo $i <= $user_rating ? 'fas' : 'far'; ?> fa-star"></i>
                    <?php endfor; ?>
                </div>
                
                <?php
                // Get user's individual ratings
                $stmt = $pdo->prepare("SELECT sr.*, u.username as rated_by_username 
                                      FROM star_ratings sr 
                                      JOIN users u ON sr.rated_by_user_id = u.id 
                                      WHERE sr.user_id = ? 
                                      ORDER BY sr.created_at DESC");
                $stmt->execute([$_SESSION['user_id']]);
                $user_ratings = $stmt->fetchAll();
                ?>
                
                <?php if (!empty($user_ratings)): ?>
                <div class="rating-history">
                    <h4>Rating History</h4>
                    <?php foreach ($user_ratings as $rating): ?>
                    <div class="rating-item">
                        <div class="rating-stars">
                            <?php for ($i = 1; $i <= 5; $i++): ?>
                                <i class="<?php echo $i <= $rating['rating'] ? 'fas' : 'far'; ?> fa-star"></i>
                            <?php endfor; ?>
                        </div>
                        <div class="rating-meta">
                            Rated by: <?php echo htmlspecialchars($rating['rated_by_username']); ?>
                            on <?php echo date('M j, Y', strtotime($rating['created_at'])); ?>
                        </div>
                        <?php if (!empty($rating['comment'])): ?>
                        <div class="rating-comment">"<?php echo htmlspecialchars($rating['comment']); ?>"</div>
                        <?php endif; ?>
                    </div>
                    <?php endforeach; ?>
                </div>
                <?php endif; ?>
            </section>

            <section class="features">
                <div class="feature-card">
                    <i class="fas fa-bolt"></i>
                    <h3>Instant Activation</h3>
                    <p>Get your hacks activated within seconds after payment confirmation ⚡</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-shield-alt"></i>
                    <h3>Undetectable</h3>
                    <p>Our advanced technology ensures complete safety from detection systems 🛡️</p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-sync-alt"></i>
                    <h3>Regular Updates</h3>
                    <p>We update our hacks immediately after every game patch 🔄</p>
                </div>
            </section>

            <section class="products">
                <h2 class="section-title">OUR PRODUCTS</h2>
                <div class="product-grid">
                    <?php foreach ($products as $product): ?>
                    <div class="product-card">
                        <div class="product-img">
                            <img src="images/xyz/xyz<?php echo $product['id']; ?>.jpg" alt="<?php echo htmlspecialchars($product['name']); ?>">
                        </div>
                        <div class="product-content">
                            <h3 class="product-title"><?php echo htmlspecialchars($product['name']); ?></h3>
                            <div class="product-desc">
                                <pre><?php echo $product['description']; ?></pre>
                            </div>
                            <div class="product-meta">
                                <div class="product-balance">Duration: <?php echo $product['duration']; ?></div>
                                <div class="product-price"><?php echo $product['price']; ?>₹</div>
                            </div>
                            <button class="buy-btn" 
                                    data-product-id="<?php echo $product['id']; ?>" 
                                    data-product-name="<?php echo htmlspecialchars($product['name']); ?>" 
                                    data-price="<?php echo $product['price']; ?>">
                                BUY NOW - <?php echo $product['price']; ?>₹
                            </button>
                        </div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </section>

            <section class="quick-links">
                <h2 class="section-title">QUICK LINKS</h2>
                <div class="links-container">
                    <a href="https://youtube.com/@kill_zone1.0?si=BjWGMAQBu6EeXumR" class="link-btn" target="_blank">
                        <div class="link-icon youtube">
                            <i class="fab fa-youtube"></i>
                        </div>
                        <span class="link-label">YouTube</span>
                    </a>
                    <a href="https://www.instagram.com/my_god_loveyou?igsh=MTllZjU3NnlqbDQxaw==" class="link-btn" target="_blank">
                        <div class="link-icon instagram">
                            <i class="fab fa-instagram"></i>
                        </div>
                        <span class="link-label">Instagram</span>
                    </a>
                    <a href="https://t.me/+NdsbCTJSlOI1Nzk9" class="link-btn" target="_blank">
                        <div class="link-icon telegram">
                            <i class="fab fa-telegram"></i>
                        </div>
                        <span class="link-label">Support</span>
                    </a>
                </div>
            </section>
        </div>

        <!-- Survive Page -->
        <div class="page" id="survive">
            <h2 class="section-title">SURVIVE PACKAGE</h2>
            <div class="about-section">
                <h3>Premium BGMI Hacks for Ultimate Survival</h3>
                <p>Our Survive package includes the most advanced and undetectable hacks for BGMI. With features like Aimbot, ESP, Wallhack, and more, you'll have the ultimate advantage in every match. 🎯</p>
                <p>Whether you're a casual player or a competitive gamer, our hacks will help you dominate the battlefield and achieve that coveted Chicken Dinner! 🏆</p>
                <p>All our products come with 24/7 support and regular updates to ensure compatibility with the latest game versions. 🔄</p>
            </div>
            
            <!-- Product list on Survive page -->
            <div class="products">
                <h2 class="section-title">OUR PRODUCTS</h2>
                <div class="product-grid">
                    <?php foreach ($products as $product): ?>
                    <div class="product-card">
                        <div class="product-img">
                            <img src="images/xyz/xyz<?php echo $product['id']; ?>.jpg" alt="<?php echo htmlspecialchars($product['name']); ?>">
                        </div>
                        <div class="product-content">
                            <h3 class="product-title"><?php echo htmlspecialchars($product['name']); ?></h3>
                            <div class="product-desc">
                                <pre><?php echo $product['description']; ?></pre>
                            </div>
                            <div class="product-meta">
                                <div class="product-balance">Duration: <?php echo $product['duration']; ?></div>
                                <div class="product-price"><?php echo $product['price']; ?>₹</div>
                            </div>
                            <button class="buy-btn" 
                                    data-product-id="<?php echo $product['id']; ?>" 
                                    data-product-name="<?php echo htmlspecialchars($product['name']); ?>" 
                                    data-price="<?php echo $product['price']; ?>">
                                BUY NOW - <?php echo $product['price']; ?>₹
                            </button>
                        </div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
        </div>

        <!-- About Page -->
        <div class="page" id="about">
            <h2 class="section-title">ABOUT BGMI LOADER</h2>
            <div class="about-content">
                <div class="about-section">
                    <h3>Who We Are</h3>
                    <p>BGMI Loader is a premium service provider for BGMI players who want to enhance their gaming experience. 🎮 We've been in the industry for over 3 years, serving thousands of satisfied customers worldwide. 🌎</p>
                </div>
                
                <div class="about-section">
                    <h3>Our Mission</h3>
                    <p>Our mission is to provide safe, reliable, and undetectable hacks that give players a competitive edge without compromising their accounts. 🛡️ We believe in fair advantage through technology! ⚙️</p>
                </div>
                
                <div class="about-section">
                    <h3>Our Technology</h3>
                    <p>We use cutting-edge technology to develop our hacks, constantly updating them to bypass the latest security measures. 🔄 Our team of developers works 24/7 to ensure our products remain undetected. 💻</p>
                </div>
                
                <div class="about-section">
                    <h3>Safety First</h3>
                    <p>Account safety is our top priority. All our products undergo rigorous testing before release to ensure they won't get your account banned. ✅ We use advanced techniques to stay under the radar. 🕵️‍♂️</p>
                </div>
                
                <div class="about-section">
                    <h3>Customer Support</h3>
                    <p>We offer 24/7 customer support to assist you with any issues or questions. 🤝 Our dedicated team is always ready to help you get the most out of our products. 💬</p>
                </div>
                
                <h3 class="section-title">BGMI GALLERY</h3>
                <div class="gallery">
                    <img src="images/abc/xyzA.jpg" alt="BGMI Gallery Image 1">
                    <img src="images/abc/xyzB.jpg" alt="BGMI Gallery Image 2">
                    <img src="images/abc/xyzC.jpg" alt="BGMI Gallery Image 3">
                    <img src="images/abc/xyzD.jpg" alt="BGMI Gallery Image 4">
                    <img src="images/abc/xyzE.jpg" alt="BGMI Gallery Image 5">
                    <img src="images/abc/xyzF.jpg" alt="BGMI Gallery Image 6">
                </div>
            </div>
        </div>

        <!-- Feedback Page -->
        <div class="page" id="feedback">
            <h2 class="section-title">USER FEEDBACK</h2>
            <div class="feedback-content">
                <div class="about-section">
                    <p>We value your feedback! See what our users have to say about our products and services. 😊 Your experience helps us improve and serve you better. 🙏</p>
                </div>
                
                <h3 class="section-title">BGMI MEDIA</h3>
                <div class="media-grid">
                    <div class="media-item"><img src="images/xyzA/xyz1a.jpg" alt="BGMI Media 1"></div>
                    <div class="media-item"><img src="images/xyzA/xyz2a.jpg" alt="BGMI Media 2"></div>
                    <div class="media-item"><img src="images/xyzA/xyz3a.jpg" alt="BGMI Media 3"></div>
                    <div class="media-item"><img src="images/xyzA/xyz4a.jpg" alt="BGMI Media 4"></div>
                    <div class="media-item"><img src="images/xyzA/xyz5a.jpg" alt="BGMI Media 5"></div>
                    <div class="media-item"><img src="images/xyzA/xyz6a.jpg" alt="BGMI Media 6"></div>
                    <div class="media-item"><img src="images/xyzA/xyz7a.jpg" alt="BGMI Media 7"></div>
                    <div class="media-item"><img src="images/xyzA/xyz8a.jpg" alt="BGMI Media 8"></div>
                    <div class="media-item"><img src="images/xyzA/xyz9a.jpg" alt="BGMI Media 9"></div>
                    <div class="media-item"><img src="images/xyzA/xyz10a.jpg" alt="BGMI Media 10"></div>
                </div>
                
                <div class="rating-section">
                    <h3>Rate Our Service</h3>
                    <p>How would you rate your experience with BGMI Loader?</p>
                    <div class="stars">
                        <i class="far fa-star" data-rating="1"></i>
                        <i class="far fa-star" data-rating="2"></i>
                        <i class="far fa-star" data-rating="3"></i>
                        <i class="far fa-star" data-rating="4"></i>
                        <i class="far fa-star" data-rating="5"></i>
                    </div>
                    <p>Your rating helps us improve our services!</p>
                </div>
            </div>
        </div>

        <!-- Support Page -->
        <div class="page" id="support">
            <h2 class="section-title">SUPPORT</h2>
            <div class="support-content">
                <div class="about-section">
                    <p>Need help? Our support team is here for you 24/7! Contact us through any of the following channels for assistance with purchases, technical issues, or general inquiries. 🤝</p>
                </div>
                
                <div class="support-grid">
                    <div class="support-card">
                        <i class="fab fa-instagram instagram-icon support-icon"></i>
                        <h3>Instagram</h3>
                        <p>Follow us for updates, tips, and announcements</p>
                        <a href="https://www.instagram.com/my_god_loveyou?igsh=MTllZjU3NnlqbDQxaw==" class="support-btn" target="_blank">View</a>
                    </div>
                    
                    <div class="support-card">
                        <i class="fab fa-telegram telegram-icon support-icon"></i>
                        <h3>Telegram</h3>
                        <p>Join our community for support and discussions</p>
                        <a href="https://t.me/+NdsbCTJSlOI1Nzk9" class="support-btn" target="_blank">View</a>
                    </div>
                    
                    <div class="support-card">
                        <i class="fab fa-youtube youtube-icon support-icon"></i>
                        <h3>YouTube</h3>
                        <p>Watch tutorials and gameplay videos</p>
                        <a href="https://youtube.com/@berry_gaming2.0?si=iUWo-oxLWTZVkWps" class="support-btn" target="_blank">View</a>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer>
        <div class="footer-content">
            <div class="footer-logo">BGMI LOADER 3.9</div>
            <p>Premium BGMI Hacks and Services</p>
            <p class="copyright">© 2025 BGMI Loader. All rights reserved. This service is not affiliated with PUBG Corporation or KRAFTON, Inc.</p>
        </div>
    </footer>

    <!-- JavaScript -->
    <script>
        // Navigation functionality
        const menuBtn = document.getElementById('menuBtn');
        const sideNav = document.getElementById('sideNav');
        const navClose = document.getElementById('navClose');
        const navLinks = document.querySelectorAll('.nav-link');
        const pages = document.querySelectorAll('.page');
        
        menuBtn.addEventListener('click', () => {
            sideNav.classList.add('active');
        });
        
        navClose.addEventListener('click', () => {
            sideNav.classList.remove('active');
        });
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = link.getAttribute('data-page');
                
                // Update active nav link
                navLinks.forEach(navLink => navLink.classList.remove('active'));
                link.classList.add('active');
                
                // Show target page
                pages.forEach(page => {
                    page.classList.remove('active');
                    if(page.id === targetPage) {
                        page.classList.add('active');
                    }
                });
                
                // Close side nav
                sideNav.classList.remove('active');
            });
        });

        // Payment functionality
        function initiatePayment(productId, productName, price) {
            // Show loading state
            const button = event.target;
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            button.disabled = true;
            
            // Create order via AJAX
            fetch('create_order.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId,
                    product_name: productName,
                    amount: price
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    var options = {
                        "key": data.key_id,
                        "amount": data.amount,
                        "currency": data.currency,
                        "name": "BGMI Loader",
                        "description": productName + " - " + data.product_duration,
                        "order_id": data.order_id,
                        "handler": function (response){
                            verifyPayment(response, productId);
                        },
                        "prefill": {
                            "name": "<?php echo $user['username']; ?>",
                            "email": "<?php echo $user['email']; ?>",
                            "contact": "9999999999"
                        },
                        "theme": {
                            "color": "#ff5722"
                        },
                        "modal": {
                            "ondismiss": function(){
                                // Reset button when modal is closed
                                button.innerHTML = originalText;
                                button.disabled = false;
                            }
                        }
                    };
                    
                    var rzp = new Razorpay(options);
                    rzp.open();
                    
                } else {
                    alert('Error: ' + data.message);
                    button.innerHTML = originalText;
                    button.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error creating order. Please try again.');
                button.innerHTML = originalText;
                button.disabled = false;
            });
        }

        function verifyPayment(paymentResponse, productId) {
            // Show loading state
            showLoading('Verifying payment...');
            
            fetch('verify_payment.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    payment_response: paymentResponse,
                    product_id: productId
                })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                
                if (data.success) {
                    showLicenseKey(data.license_key, data.download_link, data.expires_at);
                } else {
                    alert('Payment verification failed: ' + data.message);
                }
            })
            .catch(error => {
                hideLoading();
                console.error('Error:', error);
                alert('Error verifying payment. Please contact support.');
            });
        }

        function showLicenseKey(licenseKey, downloadLink, expiresAt) {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 2000;
            `;
            
            modal.innerHTML = `
                <div style="background: #121212; padding: 30px; border-radius: 15px; max-width: 500px; width: 90%; border: 2px solid #4caf50; color: white;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <i class="fas fa-check-circle" style="font-size: 3rem; color: #4caf50;"></i>
                        <h2 style="color: #4caf50; margin: 15px 0;">Purchase Successful!</h2>
                    </div>
                    
                    <div style="background: rgba(76, 175, 80, 0.2); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="margin: 0; font-size: 0.9rem;">
                            <i class="fas fa-key"></i> Your License Key:
                        </p>
                        <p style="margin: 10px 0; font-size: 1.2rem; font-weight: bold; color: #4caf50; word-break: break-all;">
                            ${licenseKey}
                        </p>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <p style="margin: 5px 0;"><i class="fas fa-download"></i> Download APK: 
                            <a href="${downloadLink}" style="color: #2196f3; text-decoration: none; font-weight: bold;">
                                Click here to download
                            </a>
                        </p>
                        <p style="margin: 5px 0;"><i class="fas fa-clock"></i> Expires: ${expiresAt}</p>
                    </div>
                    
                    <div style="background: rgba(255, 193, 7, 0.2); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="margin: 0; font-size: 0.9rem;">
                            <i class="fas fa-info-circle"></i> 
                            <strong>Important:</strong> Save your license key. You will need it to activate the application.
                        </p>
                    </div>
                    
                    <button onclick="this.closest('div').parentElement.remove()" 
                            style="background: #4caf50; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-size: 1.1rem; font-weight: bold;">
                        Close
                    </button>
                </div>
            `;
            
            document.body.appendChild(modal);
        }

        function showLoading(message = 'Processing...') {
            let loading = document.getElementById('loadingOverlay');
            if (!loading) {
                loading = document.createElement('div');
                loading.id = 'loadingOverlay';
                loading.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 3000;
                    color: white;
                    font-size: 1.2rem;
                `;
                document.body.appendChild(loading);
            }
            
            loading.innerHTML = `
                <div style="text-align: center;">
                    <i class="fas fa-spinner fa-spin" style="font-size: 3rem; margin-bottom: 20px;"></i>
                    <p>${message}</p>
                </div>
            `;
        }

        function hideLoading() {
            const loading = document.getElementById('loadingOverlay');
            if (loading) {
                loading.remove();
            }
        }

        // Star rating functionality
        const stars = document.querySelectorAll('.stars i');
        
        stars.forEach(star => {
            star.addEventListener('click', () => {
                const rating = star.getAttribute('data-rating');
                
                stars.forEach((s, index) => {
                    if(index < rating) {
                        s.classList.remove('far');
                        s.classList.add('fas');
                    } else {
                        s.classList.remove('fas');
                        s.classList.add('far');
                    }
                });
                
                alert(`Thank you for your ${rating} star rating!`);
            });
        });

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if(e.target === paymentModal) {
                paymentModal.classList.remove('active');
            }
        });
    </script>
</body>
</html>