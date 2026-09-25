<?php

// Skosmos v3.3 /entity passes a missing Accept header to Negotiator, which
// throws for an empty value. Keep this replacement strict so an upstream
// change requires review before building a new image.
$path = '/var/www/html/src/controller/EntityController.php';
$source = file_get_contents($path);
$original = '$targetFormat = $this->negotiateFormat($supportedFormats, $request->getServerConstant(\'HTTP_ACCEPT\'), $requestedFormat);';
$replacement = <<<'PHP'
$accept = $request->getServerConstant('HTTP_ACCEPT');
        if (empty($accept)) {
            $accept = '*/*';
        }
        $targetFormat = $this->negotiateFormat($supportedFormats, $accept, $requestedFormat);
PHP;

if ($source === false || substr_count($source, $original) !== 1) {
    throw new RuntimeException('Skosmos EntityController v3.3 source changed; review the Accept fallback');
}
if (file_put_contents($path, str_replace($original, $replacement, $source)) === false) {
    throw new RuntimeException('Cannot update Skosmos EntityController');
}
