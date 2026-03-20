<?php
/**
 * Macromalt Child Theme functions and definitions
 * 
 * DESIGN TRACK: Step03 - Utility & Trust Surface Refinement
 * STRATEGY: GeneratePress Hooks Strategy (LOCKED)
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

/**
 * 1. Step02 - Global Shell & IA Refinement
 */

// 1.1 Homepage Editorial Masthead (Hero) Injection
add_action( 'generate_after_header', function() {
    if ( is_front_page() && ! is_paged() ) {
        ?>
        <div class="editorial-masthead">
            <div class="grid-container">
                <h1 class="masthead-title">MACROMALT</h1>
                <p class="masthead-tagline">INSTITUTIONAL RESEARCH FOR THE GLOBAL MACRO</p>
            </div>
        </div>
        <?php
    }
}, 15 );

// 1.2 Breadcrumb & Category Badge Injection
add_action( 'generate_before_content', function() {
    if ( is_front_page() || is_search() ) {
        return;
    }

    echo '<div class="editorial-shell-meta">';
    if ( is_category() ) {
        echo '<span class="shell-badge">CATEGORY:</span> ' . single_cat_title( '', false );
    } elseif ( is_single() ) {
        echo '<span class="shell-badge">INSIGHT:</span> ';
        the_category( ', ' );
    }
    echo '</div>';
}, 5 );

/**
 * 2. Step03 - Utility & Trust Surface Refinement
 */

// 2.1 Disclosure & Methodology Box (Single Posts Only)
add_action( 'generate_before_content', function() {
    if ( is_single() && ! is_page() ) {
        $disclosure_text = '';
        if ( has_category( 'analysis' ) ) {
            $disclosure_text = '본 분석은 공개적으로 확인 가능한 경제지표, 기업 공시, 실적 자료, 정책 발표, 그리고 신뢰 가능한 리서치 자료를 바탕으로 작성되었다.';
        } elseif ( has_category( 'picks' ) ) {
            $disclosure_text = '본 콘텐츠는 정보 제공 및 해석 목적의 에디토리얼 리서치이며, 특정 자산에 대한 투자 권유를 의미하지 않는다. 시장 환경은 빠르게 변할 수 있으며, 최종 투자 판단과 그 결과에 대한 책임은 이용자 본인에게 있다.';
        } else {
            // Default or Fallback Text
            $disclosure_text = '본 콘텐츠는 정보 제공을 목적으로 하는 에디토리얼 리서치이며, 최종 투자 판단과 결과에 대한 책임은 이용자 본인에게 있습니다.';
        }

        echo '<div class="editorial-disclosure-box">
                <span class="disclosure-heading">DISCLOSURE & METHODOLOGY</span>
                ' . esc_html( $disclosure_text ) . '
              </div>';
    }
}, 10 );

// 2.2 Search Results Header
add_action( 'generate_before_main_content', function() {
    if ( is_search() ) {
        echo '<div class="search-results-label">SEARCHING THE MACROMALT ARCHIVE:</div>';
    }
}, 5 );

// 2.3 Footer Trust Micro-layer (Append)
add_action( 'generate_after_footer_content', function() {
    echo '<div class="footer-trust-layer">
            © 2026 MACROMALT. ALL RIGHTS RESERVED. INSTITUTIONAL RESEARCH FOR THE GLOBAL MACRO.
          </div>';
}, 20 );

// 2.4 Read More Text Refinement (Robust Filters)
add_filter( 'generate_excerpt_more', function( $more ) {
    return ' ...';
}, 20 );

add_filter( 'generate_content_more_link_output', 'macromalt_customize_read_more', 20 );
add_filter( 'generate_excerpt_more_output', 'macromalt_customize_read_more', 20 );
function macromalt_customize_read_more() {
    return sprintf(
        '<p class="read-more-container"><a title="%1$s" class="read-more" href="%2$s">%3$s</a></p>',
        the_title_attribute( 'echo=0' ),
        esc_url( get_permalink() ),
        __( 'FULL ANALYSIS →', 'generatepress' )
    );
}

/**
 * 3. Step04 - Seasonal Layer
 */

// 3.1 Deterministic Seasonal Class (WP Timezone)
add_filter( 'body_class', function( $classes ) {
    // WordPress 로컬 타임존 기반 월 식별 (jan, feb...)
    $month = strtolower( current_time( 'M' ) ); 
    $classes[] = 'mm-season-' . $month;
    return $classes;
} );

/**
 * 4. Enqueue Parent Styles
 */
add_action( 'wp_enqueue_scripts', function() {
    wp_enqueue_style( 'generatepress-style', get_template_directory_uri() . '/style.css' );
}, 1 );
?>
